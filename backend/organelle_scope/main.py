from __future__ import annotations

import math

import argparse
import hashlib
import io
import json
import os
import secrets
import shutil
from pathlib import Path
from threading import Lock
from typing import Literal
from uuid import UUID, uuid4

import numpy as np
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from PIL import Image
from pydantic import BaseModel, Field

from organelle_scope.display_luts import display_colors
from organelle_scope.roi_analysis import AnalysisRequest
from organelle_scope.processing import ProcessingConfig, process_plane, provenance, estimate_background, processing_diagnostics, prepared_plane
from organelle_scope import __version__
from organelle_scope.image_io import ImageError, ImageInfo, inspect_tiff, read_plane


class InspectOptions(BaseModel):
    series_index: int = Field(default=0, ge=0)
    axes: str | None = None
    spacing_um: dict[str, float] = Field(default_factory=dict)


class ChannelNames(BaseModel):
    labels: list[str] = Field(min_length=1, max_length=4)
    expected_image_info: dict


def create_app(data_dir: Path, token: str) -> FastAPI:
    app = FastAPI(title="OrganelleScope", version=__version__)
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "null"],
                       allow_methods=["GET", "POST", "DELETE"], allow_headers=["Content-Type", "X-Session-Token"],
                       expose_headers=["X-Volume-Shape", "X-Volume-Spacing", "X-Volume-Units"])
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
        if record.get("import_schema") != 2 or record.get("info",{}).get("acquisition",{}).get("color_model_checked") != "yes":
            options = InspectOptions.model_validate(record.get("options", {}))
            revised = inspect_tiff(folder / "source.tiff", options.series_index, options.axes, options.spacing_um)
            revised.filename = record["info"]["filename"]
            record.update(info=revised.model_dump(), import_schema=2)
            save_record(folder, record)
        return folder, record, ImageInfo.model_validate(record["info"])

    def save_record(folder: Path, record: dict) -> None:
        temp = folder / "metadata.tmp"
        temp.write_text(json.dumps(record, indent=2, allow_nan=False))
        temp.replace(folder / "metadata.json")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    @app.get("/api/ready", dependencies=[Depends(authorized)])
    def session_ready() -> dict:
        return {"status": "ok", "service": "OrganelleScope", "version": __version__}

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
            record = {"id": image_id, "sha256": digest.hexdigest(), "info": info.model_dump(), "options": {}, "import_schema": 2}
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

    @app.post('/api/images/{image_id}/channels', dependencies=[Depends(authorized)])
    def channel_names(image_id: str, options: ChannelNames) -> dict:
        with lock:
            folder, record, info = stored(image_id)
            if options.expected_image_info != record['info']:
                raise HTTPException(409, 'Image settings changed. Reopen the image before naming channels.')
            labels = [label.strip() for label in options.labels]
            if len(labels) != info.dimensions['C'] or any(not label or len(label)>120 or any(ord(c)<32 for c in label) for label in labels):
                raise HTTPException(422, 'Give every stored channel a nonempty name of at most 120 characters.')
            if len(set(labels)) != len(labels):
                raise HTTPException(422, 'Use distinct channel names; include the dye when markers repeat.')
            if labels != info.channel_labels:
                record.setdefault('original_channel_labels', list(info.channel_labels))
                record['info']['channel_labels'] = labels
                record['channel_annotation'] = {'source': 'User assigned; not inferred from dye or colour', 'labels': labels, 'series_index': info.series_index}
                save_record(folder, record)
            return record

    @app.get('/api/images/{image_id}/quality', dependencies=[Depends(authorized)])
    def acquisition_quality(image_id: str, z: int = 0, lateral_resolution_um:float|None=None, axial_resolution_um:float|None=None, detector_ceiling:int|None=None) -> dict:
        folder, record, info = stored(image_id)
        from organelle_scope.acquisition_quality import plane_quality,sampling_review
        try:
            if any(v is not None and (not math.isfinite(v) or v<=0 or v>1000) for v in [lateral_resolution_um,axial_resolution_um]):raise ImageError('Supply a finite positive nominal resolution up to 1000 µm.')
            rows = [plane_quality(read_plane(folder/'source.tiff', info, c, z), c, label,detector_ceiling) for c, label in enumerate(info.channel_labels)]
        except (ImageError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc
        return {'source_sha256': record['sha256'], 'image_info': record['info'], 'z': z, 'channels': rows,'sampling_review':sampling_review(info,lateral_resolution_um,axial_resolution_um),
                'scope': 'Exact raw pixels of the selected XY plane only, not the whole stack or an ROI. Storage-ceiling counts do not establish detector saturation; acquisition bit depth/gain and controls require review.',
                'calibration_notes': [f'{a} sampling is unknown or conflicting.' for a in 'XYZ' if (a!='Z' or info.dimensions['Z']>1) and (info.calibration[a].value_um is None or info.calibration[a].conflict)]}

    @app.post("/api/images/{image_id}/inspect", dependencies=[Depends(authorized)])
    def reinspect(image_id: str, options: InspectOptions) -> dict:
        with lock:
            folder, record, _ = stored(image_id)
            try:
                info = inspect_tiff(folder / "source.tiff", options.series_index, options.axes, options.spacing_um)
            except (ImageError, ValueError) as exc:
                raise HTTPException(422, str(exc)) from exc
            info.filename = record["info"]["filename"]
            if info.series_index == record['info']['series_index'] and info.axes == record['info']['axes'] and info.dimensions['C'] == record['info']['dimensions']['C'] and record.get('channel_annotation'):
                info.channel_labels = record['channel_annotation']['labels']
            else:
                record.pop('channel_annotation', None)
                record.pop('original_channel_labels', None)
            record.update(info=info.model_dump(), options=options.model_dump())
            save_record(folder, record)
            return record

    @app.get("/api/images/{image_id}/analysis", dependencies=[Depends(authorized)])
    def saved_analysis(image_id: str) -> dict:
        folder, record, _ = stored(image_id)
        path = folder / "analysis.json"
        if not path.exists():
            raise HTTPException(404, "No saved ROI analysis yet.")
        result = json.loads(path.read_text())
        if result["source_sha256"] != record["sha256"]:
            raise HTTPException(409, "Image source changed; run the ROI analysis again.")
        if result["image_info"] != record["info"]:
            def numerical_metadata(value):
                value=json.loads(json.dumps(value));value.pop('warnings',None)
                acquisition=value.get('acquisition',{})
                for key in ('color_model_checked','stored_color_model'):acquisition.pop(key,None)
                return value
            if numerical_metadata(result['image_info'])!=numerical_metadata(record['info']):
                raise HTTPException(409, "Image settings changed; run the ROI analysis again.")
            # Enrich the returned view only. The original on-disk result and metadata remain intact.
            result['original_image_info']=result['image_info']
            result['image_info']=record['info']
            result['metadata_notice']='Import quality notes updated; source hash, axes, calibration and numerical metadata are unchanged. Original report metadata is retained in original_image_info.'
        return result

    @app.post("/api/images/{image_id}/analysis", dependencies=[Depends(authorized)])
    def measure(image_id: str, options: AnalysisRequest) -> dict:
        with lock:
            folder, record, info = stored(image_id)
            from organelle_scope.analysis_service import compute_analysis
            try:result=compute_analysis(folder,record,info,options)
            except (ImageError,ValueError) as exc:raise HTTPException(422,str(exc)) from exc
            temp = folder / "analysis.tmp"
            temp.write_text(json.dumps(result, indent=2, allow_nan=False))
            temp.replace(folder / "analysis.json")
            return result

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
    def preview(image_id: str, z: int = 0, luts: str | None = None, contrast: Literal['native','auto'] = 'native') -> Response:
        folder, _, info = stored(image_id)
        output = np.zeros((info.dimensions["Y"], info.dimensions["X"], 3), np.float32)
        try:
            colors = display_colors(luts, info.dimensions["C"])
            for c in range(info.dimensions["C"]):
                plane_data = read_plane(folder / "source.tiff", info, c, z)
                high = float(2**info.bit_depth-1) if contrast == 'native' else (float(np.percentile(plane_data[::4, ::4], 99.5)) or float(plane_data.max()) or 1.)
                output += np.clip(plane_data / high, 0, 1)[..., None] * colors[c]
        except (ImageError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc
        image = Image.fromarray((np.clip(output, 0, 1) * 255).astype(np.uint8))
        image.thumbnail((1024, 1024))
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return Response(buf.getvalue(), media_type="image/png")

    def processing_channels(image_id: str, z: int, config: ProcessingConfig):
        folder, _, info = stored(image_id)
        config.validate_channels(info.dimensions["C"], info.bit_depth)
        return info, [read_plane(folder / "source.tiff", info, c, z) for c in range(info.dimensions["C"])]

    @app.post("/api/images/{image_id}/processing/recipe", dependencies=[Depends(authorized)])
    def processing_recipe(image_id: str, config: ProcessingConfig) -> dict:
        _, record, info = stored(image_id)
        try:
            config.validate_channels(info.dimensions["C"], info.bit_depth)
        except ImageError as exc:
            raise HTTPException(422, str(exc)) from exc
        return {"source_sha256": record["sha256"], "image_info": record["info"], **provenance(config,data_dir)}

    @app.post("/api/images/{image_id}/processing/plane", dependencies=[Depends(authorized)])
    def processed_plane(image_id: str, config: ProcessingConfig, z: int = 0, channel: int = 0) -> Response:
        folder, _, info = stored(image_id)
        try:
            config.validate_channels(info.dimensions["C"], info.bit_depth)
            data = process_plane(read_plane(folder / "source.tiff", info, channel, z), config, channel, data_dir,z)
        except (ImageError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc
        return Response(np.ascontiguousarray(data, dtype="<f4").tobytes(), media_type="application/octet-stream")

    @app.post("/api/images/{image_id}/processing/preview", dependencies=[Depends(authorized)])
    def processing_preview(image_id: str, config: ProcessingConfig, z: int = 0, view: Literal['comparison','background','residual'] = 'comparison', luts: str | None = None) -> Response:
        try:
            info, channels = processing_channels(image_id, z, config)
            colors = display_colors(luts, info.dimensions["C"])
            raw = np.zeros((info.dimensions["Y"], info.dimensions["X"], 3), np.float32)
            corrected = np.zeros_like(raw)
            auxiliary = np.zeros_like(raw)
            for c, source in enumerate(channels):
                # Identical raw-derived contrast in both panels: no misleading independent rescaling.
                high = float(np.percentile(source[::4, ::4], 99.5)) or float(source.max()) or 1.
                raw += np.clip(source/high, 0, 1)[..., None]*colors[c]
                processed=process_plane(source, config, c,data_dir,z)
                corrected += np.clip(processed/high, 0, 1)[..., None]*colors[c]
                if view=='background':auxiliary += np.clip(estimate_background(prepared_plane(source,config,c,data_dir,z),config,c)/high,0,1)[...,None]*colors[c]
                elif view=='residual':auxiliary += np.abs(source.astype(np.float32)-processed)[...,None]/high/len(channels)
            panels = []
            for data in ((raw, corrected) if view=='comparison' else (auxiliary,)):
                image = Image.fromarray((np.clip(data, 0, 1)*255).astype(np.uint8))
                image.thumbnail((768, 768));panels.append(image)
            comparison = Image.new("RGB", (sum(p.width for p in panels), panels[0].height))
            comparison.paste(panels[0], (0, 0))
            if len(panels)>1:comparison.paste(panels[1], (panels[0].width, 0))
            buf = io.BytesIO();comparison.save(buf, format="PNG")
            return Response(buf.getvalue(), media_type="image/png")
        except (ImageError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post('/api/images/{image_id}/processing/diagnostics',dependencies=[Depends(authorized)])
    def processing_quality(image_id:str,config:ProcessingConfig,z:int=0):
        try:
            info,channels=processing_channels(image_id,z,config)
            _,record,_=stored(image_id)
            rows=[{'channel':c,'label':info.channel_labels[c],**processing_diagnostics(raw,process_plane(raw,config,c,data_dir,z),estimate_background(prepared_plane(raw,config,c,data_dir,z),config,c))} for c,raw in enumerate(channels)]
            return {'source_sha256':record['sha256'],'z_index':z,'processing':provenance(config,data_dir),'channels':rows,
                    'scope':'Full XY-plane descriptive differences. Residual structure can indicate removed signal or noise; it does not prove restoration quality or optical resolution.'}
        except (ImageError,ValueError) as exc:raise HTTPException(422,str(exc)) from exc

    @app.get("/api/images/{image_id}/volume", dependencies=[Depends(authorized)])
    def volume(image_id: str, channel: int = 0, units: str = "physical") -> Response:
        folder, _, info = stored(image_id)
        if units not in {"physical", "voxel"}:
            raise HTTPException(422, "Volume units must be physical or voxel.")
        if units == "physical" and not info.calibrated(volume=True):
            raise HTTPException(422, "Confirm X, Y and Z spacing before calibrated 3D rendering.")
        if info.dimensions["Z"] < 2:
            raise HTTPException(422, "A 3D volume requires at least two Z planes.")
        # Copy each reduced slice so its view cannot retain a full source plane.
        # Bounded display-only preview. Source planes remain unchanged for measurements.
        sx = max(1, int(np.ceil(info.dimensions["X"] / 128)))
        sy = max(1, int(np.ceil(info.dimensions["Y"] / 128)))
        sz = max(1, int(np.ceil(info.dimensions["Z"] / 64)))
        try:
            data = np.stack([read_plane(folder / "source.tiff", info, channel, z)[::sy, ::sx].copy()
                             for z in range(0, info.dimensions["Z"], sz)])
        except (ImageError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc
        spacing = [(info.calibration[a].value_um if units == "physical" else 1.) * s for a, s in zip("XYZ", (sx, sy, sz))]
        return Response(np.ascontiguousarray(data, dtype="<u2").tobytes(), media_type="application/octet-stream", headers={
            "X-Volume-Shape": json.dumps(list(data.shape)), "X-Volume-Spacing": json.dumps(spacing),
            "X-Volume-Units": "um" if units == "physical" else "voxel"
        })

    from organelle_scope.research_routes import register_research
    from organelle_scope.evidence import register_evidence
    register_research(app, stored, authorized)
    from organelle_scope.analysis_jobs import register_analysis_jobs
    register_analysis_jobs(app, stored, authorized)
    from organelle_scope.review_report import register_review_report
    register_review_report(app, stored, authorized)
    query_evidence = register_evidence(app, data_dir, authorized)
    from organelle_scope.projects import register_projects
    load_project = register_projects(app, data_dir, stored, authorized)
    from organelle_scope.assistant import register_assistant
    register_assistant(app, data_dir, authorized, load_project, query_evidence, stored)
    from organelle_scope.batch import register_batch
    register_batch(app, data_dir, stored, image_dir, authorized)
    from organelle_scope.segmentation import register_segmentation
    register_segmentation(app,stored,authorized)
    from organelle_scope.experiments import register_experiments
    register_experiments(app,data_dir,authorized)
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
