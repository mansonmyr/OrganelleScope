from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import secrets
import shutil
from pathlib import Path
from threading import Lock
from uuid import UUID, uuid4

import numpy as np
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from PIL import Image
from pydantic import BaseModel, Field

from organelle_scope import __version__
from organelle_scope.image_io import ImageError, ImageInfo, inspect_tiff, read_plane


class InspectOptions(BaseModel):
    series_index: int = Field(default=0, ge=0)
    axes: str | None = None
    spacing_um: dict[str, float] = Field(default_factory=dict)


def create_app(data_dir: Path, token: str) -> FastAPI:
    app = FastAPI(title="OrganelleScope", version=__version__)
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "null"],
                       allow_methods=["GET", "POST", "DELETE"], allow_headers=["Content-Type", "X-Session-Token"],
                       expose_headers=["X-Volume-Shape", "X-Volume-Spacing"])
    data_dir.mkdir(parents=True, exist_ok=True)
    lock = Lock()

    def authorized(x_session_token: str = Header(default="")) -> None:
        if not secrets.compare_digest(x_session_token, token):
            raise HTTPException(401, "This request does not belong to the local application session.")

    def image_dir(image_id: str) -> Path:
        try:
            UUID(image_id)
        except ValueError:
            raise HTTPException(404, "Image not found.")
        folder = data_dir / image_id
        if not (folder / "metadata.json").is_file():
            raise HTTPException(404, "Image not found.")
        return folder

    def stored(image_id: str) -> tuple[Path, dict, ImageInfo]:
        folder = image_dir(image_id)
        record = json.loads((folder / "metadata.json").read_text())
        if record.get("import_schema") != 1:
            options = InspectOptions.model_validate(record.get("options", {}))
            revised = inspect_tiff(folder / "source.tiff", options.series_index, options.axes, options.spacing_um)
            revised.filename = record["info"]["filename"]
            record.update(info=revised.model_dump(), import_schema=1)
            save_record(folder, record)
        return folder, record, ImageInfo.model_validate(record["info"])

    def save_record(folder: Path, record: dict) -> None:
        temp = folder / "metadata.tmp"
        temp.write_text(json.dumps(record, indent=2, allow_nan=False))
        temp.replace(folder / "metadata.json")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    @app.post("/api/images", dependencies=[Depends(authorized)])
    def import_image(file: UploadFile = File(...)) -> dict:
        name = Path(file.filename or "image.tiff").name
        if Path(name).suffix.lower() not in {".tif", ".tiff"}:
            raise HTTPException(422, "Select a TIFF or OME-TIFF image.")
        image_id = str(uuid4())
        folder = data_dir / image_id
        folder.mkdir()
        try:
            digest = hashlib.sha256()
            size = 0
            with (folder / "source.tiff").open("wb") as dst:
                while chunk := file.file.read(1024 * 1024):
                    size += len(chunk)
                    if size > 8 * 1024**3:
                        raise ImageError("This import exceeds the current 8 GiB file limit.")
                    digest.update(chunk)
                    dst.write(chunk)
            info = inspect_tiff(folder / "source.tiff")
            info.filename = name
            record = {"id": image_id, "sha256": digest.hexdigest(), "info": info.model_dump(), "options": {}, "import_schema": 1}
            save_record(folder, record)
            return record
        except Exception as exc:
            shutil.rmtree(folder)
            if isinstance(exc, (ImageError, ValueError, OSError)):
                raise HTTPException(422, str(exc)) from exc
            raise
        finally:
            file.file.close()

    @app.get("/api/images", dependencies=[Depends(authorized)])
    def recent_images() -> list[dict]:
        records = []
        for p in sorted(data_dir.glob("*/metadata.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
            try:
                records.append(stored(p.parent.name)[1])
            except (OSError, ValueError, HTTPException):
                continue
        return records

    @app.get("/api/images/{image_id}", dependencies=[Depends(authorized)])
    def metadata(image_id: str) -> dict:
        return stored(image_id)[1]

    @app.post("/api/images/{image_id}/inspect", dependencies=[Depends(authorized)])
    def reinspect(image_id: str, options: InspectOptions) -> dict:
        with lock:
            folder, record, _ = stored(image_id)
            try:
                info = inspect_tiff(folder / "source.tiff", options.series_index, options.axes, options.spacing_um)
            except (ImageError, ValueError) as exc:
                raise HTTPException(422, str(exc)) from exc
            info.filename = record["info"]["filename"]
            record.update(info=info.model_dump(), options=options.model_dump())
            save_record(folder, record)
            return record

    @app.get("/api/images/{image_id}/plane", dependencies=[Depends(authorized)])
    def plane(image_id: str, z: int = 0, channel: int = 0) -> Response:
        folder, _, info = stored(image_id)
        try:
            data = read_plane(folder / "source.tiff", info, channel, z)
        except (ImageError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc
        # Native unsigned pixels, little-endian, for quantitative profile sampling.
        dtype = np.dtype("<u2") if info.bit_depth == 16 else np.dtype("u1")
        return Response(np.ascontiguousarray(data, dtype=dtype).tobytes(), media_type="application/octet-stream")

    @app.get("/api/images/{image_id}/preview", dependencies=[Depends(authorized)])
    def preview(image_id: str, z: int = 0) -> Response:
        folder, _, info = stored(image_id)
        colors = np.array([[1, .12, .25], [.1, 1, .65], [.2, .45, 1], [.8, .8, .8]])
        output = np.zeros((info.dimensions["Y"], info.dimensions["X"], 3), np.float32)
        try:
            for c in range(info.dimensions["C"]):
                plane_data = read_plane(folder / "source.tiff", info, c, z)
                high = float(np.percentile(plane_data[::4, ::4], 99.5)) or float(plane_data.max()) or 1.
                output += np.clip(plane_data / high, 0, 1)[..., None] * colors[c]
        except (ImageError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc
        image = Image.fromarray((np.clip(output, 0, 1) * 255).astype(np.uint8))
        image.thumbnail((1024, 1024))
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return Response(buf.getvalue(), media_type="image/png")

    @app.get("/api/images/{image_id}/volume", dependencies=[Depends(authorized)])
    def volume(image_id: str, channel: int = 0) -> Response:
        folder, _, info = stored(image_id)
        if not info.calibrated(volume=True):
            raise HTTPException(422, "Confirm X, Y and Z spacing before calibrated 3D rendering.")
        if info.dimensions["Z"] < 2:
            raise HTTPException(422, "A 3D volume requires at least two Z planes.")
        # Bounded display-only preview. Source planes remain unchanged for measurements.
        sx = max(1, int(np.ceil(info.dimensions["X"] / 128)))
        sy = max(1, int(np.ceil(info.dimensions["Y"] / 128)))
        sz = max(1, int(np.ceil(info.dimensions["Z"] / 64)))
        try:
            data = np.stack([read_plane(folder / "source.tiff", info, channel, z)[::sy, ::sx]
                             for z in range(0, info.dimensions["Z"], sz)])
        except (ImageError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc
        spacing = [info.calibration[a].value_um * s for a, s in zip("XYZ", (sx, sy, sz))]
        return Response(np.ascontiguousarray(data, dtype="<u2").tobytes(), media_type="application/octet-stream", headers={
            "X-Volume-Shape": json.dumps(list(data.shape)), "X-Volume-Spacing": json.dumps(spacing)
        })

    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--data-dir", type=Path, default=Path.home() / ".organellescope" / "images")
    args = parser.parse_args()
    token = os.environ.get("ORGANELLESCOPE_SESSION_TOKEN")
    if not token:
        parser.error("ORGANELLESCOPE_SESSION_TOKEN must be set by the desktop launcher or development environment.")
    import uvicorn
    uvicorn.run(create_app(args.data_dir, token), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
