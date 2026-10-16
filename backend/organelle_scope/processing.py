"""Deterministic, per-channel XY processing; source pixels are never modified."""
from typing import Annotated, Literal
import hashlib
import json
import numpy as np
import scipy
from scipy.ndimage import grey_opening, gaussian_filter
from pydantic import BaseModel, ConfigDict, Field
from organelle_scope.image_io import ImageError


class ProcessingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    background: Literal["none", "constant", "opening"] = "none"
    offsets: list[Annotated[float, Field(ge=0, le=65535, allow_inf_nan=False)]] = Field(default_factory=list, max_length=4)
    radius_px: int = Field(default=20, ge=1, le=512)
    sigma_px: float = Field(default=0, ge=0, le=5, allow_inf_nan=False)

    @property
    def active(self):
        return self.background != "none" or self.sigma_px > 0

    def validate_channels(self, count: int, bit_depth: int):
        if self.background == "constant" and (len(self.offsets) != count or
            any(not np.isfinite(x) or x < 0 or x > 2**bit_depth-1 for x in self.offsets)):
            raise ImageError("Provide one finite background offset per channel within the source intensity range.")


def process_plane(source: np.ndarray, config: ProcessingConfig, channel: int) -> np.ndarray:
    data = source.astype(np.float32, copy=True)
    if config.background == "constant":
        data -= config.offsets[channel]
    elif config.background == "opening":
        data -= grey_opening(data, size=(2*config.radius_px+1,)*2, mode="reflect")
    np.maximum(data, 0, out=data)
    if config.sigma_px > 0:
        data = gaussian_filter(data, sigma=config.sigma_px, mode="reflect", truncate=4.0)
    return data


def provenance(config: ProcessingConfig) -> dict:
    recipe = {"algorithm": "xy-processing-1", "settings": config.model_dump(),
              "numpy_version": np.__version__, "scipy_version": scipy.__version__,
              "order": ["background subtraction", "clip negatives to zero", "optional Gaussian smoothing"],
              "boundary": "reflect", "dtype": "float32" if config.active else "native unsigned source", "axes": "XY independently per Z and channel",
              "opening_footprint": "flat square, width 2*radius_px+1", "gaussian_truncate": 4.0}
    recipe["recipe_sha256"] = hashlib.sha256(json.dumps(recipe, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return recipe
