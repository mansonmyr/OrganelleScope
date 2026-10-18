"""TIFF inspection without guessing that a short dimension is a channel axis.

Inspection reads headers only. Viewing decodes one TIFF page at a time where
possible; unusual multi-dimensional page layouts are rejected explicitly.
All quantitative values retain their native uint8/uint16 units.
"""
from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Literal

import numpy as np
import tifffile
from pydantic import BaseModel, Field


class ImageError(ValueError):
    pass


class CalibrationValue(BaseModel):
    value_um: float | None = None
    source: str = "unavailable"
    candidates: dict[str, float] = Field(default_factory=dict)
    conflict: bool = False


class ImageInfo(BaseModel):
    filename: str
    series_index: int
    series_count: int
    source_axes: str
    axes: str
    shape: list[int]
    dtype: str
    bit_depth: int
    dimensions: dict[str, int]
    channel_labels: list[str]
    calibration: dict[str, CalibrationValue]
    warnings: list[str]
    needs_axis_confirmation: bool
    acquisition: dict[str, str] = Field(default_factory=dict)
    decoded_bytes: int

    def calibrated(self, volume: bool = False) -> bool:
        axes = "XYZ" if volume and self.dimensions["Z"] > 1 else "XY"
        return all(self.calibration[a].value_um is not None for a in axes)


_UNITS = {"µm": 1., "μm": 1., "um": 1., "micron": 1., "microns": 1.,
          "nm": .001, "mm": 1000., "cm": 10000., "m": 1e6}


def _unit_key(unit: object) -> str:
    # ImageJ writes Unicode symbols either literally or as ASCII Unicode escapes.
    return str(unit).strip().lower().replace(r"\u00b5", "µ").replace(r"\u03bc", "μ")


def _physical(value: object, unit: str | None) -> float | None:
    try:
        result = float(value) * _UNITS[_unit_key(unit)]
        return result if math.isfinite(result) and result > 0 else None
    except (ValueError, TypeError, KeyError):
        return None


def _resolve(candidates: dict[str, float], warnings: list[str], axis: str) -> CalibrationValue:
    if not candidates:
        warnings.append(f"{axis} spacing is missing or has unsupported units. Physical distances along this axis are unavailable until calibrated.")
        return CalibrationValue()
    if list(candidates) == ["TIFF resolution"]:
        warnings.append(f"{axis} has only generic TIFF resolution tags, which may describe print DPI rather than specimen scale. Confirm microscope pixel size before physical measurements.")
        return CalibrationValue(source="TIFF resolution (unconfirmed)", candidates=candidates)
    source, value = next(iter(candidates.items()))
    conflict = any(not math.isclose(value, v, rel_tol=.01, abs_tol=1e-9) for v in candidates.values())
    if conflict:
        warnings.append(f"Conflicting {axis} spacing metadata. Confirm a value before physical measurements.")
    return CalibrationValue(value_um=None if conflict else value, source="conflict" if conflict else source,
                            candidates=candidates, conflict=conflict)


def inspect_tiff(path: Path, series_index: int = 0, axes_override: str | None = None,
                 spacing_override: dict[str, float] | None = None) -> ImageInfo:
    warnings: list[str] = []
    candidates: dict[str, dict[str, float]] = {a: {} for a in "XYZ"}
    acquisition: dict[str, str] = {}
    labels: list[str] = []
    with tifffile.TiffFile(path) as tf:
        if not 0 <= series_index < len(tf.series):
            raise ImageError("The selected image series does not exist.")
        series = tf.series[series_index]
        if np.dtype(series.dtype) not in (np.dtype("uint8"), np.dtype("uint16")):
            raise ImageError(f"Expected uint8 or uint16 pixels; found {series.dtype}.")
        source_axes = series.axes
        axes = (axes_override or source_axes).upper()
        if len(axes) != len(series.shape) or (axes_override and len(set(axes)) != len(axes)):
            raise ImageError("Axis order must contain one unique letter per dimension.")
        if "Y" not in axes or "X" not in axes:
            raise ImageError("TIFF must contain X and Y image axes.")
        if axes_override and any(a not in "TCZYX" for a in axes):
            raise ImageError("Confirmed axis order may contain only T, C, Z, Y and X.")
        ambiguous = any(a not in "TCZYX" and n > 1 for a, n in zip(axes, series.shape))
        if ambiguous:
            warnings.append(f"Axis order {source_axes} is ambiguous for scientific channels. Confirm the axis order; no planes have been discarded.")
        dims = {a: int(series.shape[axes.index(a)]) if a in axes else 1 for a in "TCZYX"}
        if dims["C"] > 4:
            raise ImageError("The first release supports at most four channels.")
        if dims["T"] > 1:
            warnings.append("Time series are not supported in this milestone; export a single time point. No frame is selected automatically.")
        if len(tf.series) > 1:
            warnings.append(f"This file contains {len(tf.series)} image series; inspecting series {series_index + 1} only.")

        if tf.ome_metadata:
            try:
                root = ET.fromstring(tf.ome_metadata)
                images = root.findall("{*}Image")
                if series_index < len(images):
                    image = images[series_index]
                    pixels = image.find("{*}Pixels")
                    if pixels is not None:
                        for a in "XYZ":
                            key = f"PhysicalSize{a}"
                            v = _physical(pixels.get(key), pixels.get(key + "Unit", "µm"))
                            if v is not None:
                                candidates[a]["OME Pixels"] = v
                        labels = [c.get("Name") or c.get("ID") or f"Channel {i + 1}"
                                  for i, c in enumerate(pixels.findall("{*}Channel"))]
                        # Nonuniform acquired plane positions cannot be represented by one Z step.
                        positions: dict[int, set[float]] = {}
                        for p in pixels.findall("{*}Plane"):
                            try:
                                factor = _UNITS[p.get("PositionZUnit", "µm")]
                                pos = float(p.attrib["PositionZ"]) * factor
                                if math.isfinite(pos):
                                    positions.setdefault(int(p.get("TheZ", "0")), set()).add(pos)
                            except (ValueError, KeyError):
                                pass
                        if len(positions) > 1:
                            z_items = sorted((k, sum(v) / len(v)) for k, v in positions.items())
                            steps = [(b[1] - a[1]) / (b[0] - a[0]) for a, b in zip(z_items, z_items[1:])]
                            if any(len(v) > 1 for v in positions.values()) or not np.allclose(steps, steps[0], rtol=.01, atol=1e-6) or steps[0] <= 0:
                                warnings.append("Nonuniform or inconsistent OME Z positions require review before volume measurements.")
                                candidates["Z"].clear()
                            else:
                                candidates["Z"]["OME Plane positions"] = steps[0]
                    acquisition["metadata_format"] = "OME"
                    for tag in ("Objective", "Detector", "Microscope"):
                        # Report descriptors, never infer measured resolution from specifications.
                        nodes = root.findall(f".//{{*}}{tag}")
                        if nodes:
                            acquisition[tag.lower()] = "; ".join(str(dict(n.attrib)) for n in nodes)
            except ET.ParseError:
                warnings.append("OME XML could not be parsed; inspect calibration manually.")

        ij = tf.imagej_metadata or {}
        # Bio-Formats/Fiji exports may retain the original acquisition's Info block
        # after cropping/extracting a channel. Stored TIFF geometry remains authoritative.
        inherited={a:int(n) for a,n in re.findall(r"^\s*Size([TCZYX])\s*=\s*(\d+)\s*$",str(ij.get('Info','')),re.MULTILINE)}
        mismatches=[f"{a}: Info {n}, stored {dims[a]}" for a,n in inherited.items() if n!=dims[a]]
        if mismatches:
            acquisition['imagej_info_dimension_mismatch']='; '.join(mismatches)
            warnings.append('Inherited ImageJ Info dimensions differ from the stored TIFF ('+'; '.join(mismatches)+'). This may be an extracted channel, crop or projection. Stored pixels/axes are used; verify export history and channel identity. Missing original channels are not recovered.')
        page = series.pages[0]
        unit_tag = page.tags.get("ResolutionUnit")
        tiff_unit = int(unit_tag.value) if unit_tag is not None else 1
        unit = "cm" if tiff_unit == 3 else None
        unit_factor = 25400. if tiff_unit == 2 else _UNITS.get(unit or "")
        if ij.get("unit"):
            unit_factor = _UNITS.get(_unit_key(ij["unit"])) if tiff_unit == 1 else unit_factor
        for a in "XY":
            tag = page.tags.get(f"{a}Resolution")
            if tag is not None and unit_factor:
                numerator, denominator = tag.value
                if numerator > 0 and denominator > 0:
                    candidates[a]["ImageJ resolution" if ij and tiff_unit == 1 else "TIFF resolution"] = unit_factor * denominator / numerator
        v = _physical(ij.get("spacing"), ij.get("unit"))
        if v is not None:
            candidates["Z"]["ImageJ spacing"] = v
        if ij:
            acquisition.setdefault("metadata_format", "ImageJ")
        acquisition['color_model_checked']='yes'
        if getattr(series.pages[0].photometric,'name','') == 'RGB':
            acquisition['stored_color_model']='RGB components'
            warnings.append('This TIFF stores RGB color components. They may be a rendered/composite export rather than independent raw microscope channels. Verify the acquisition channel mapping before quantitative biological interpretation; use the original channel data when available.')
        calibration = {a: _resolve(candidates[a], warnings, a) for a in "XYZ"}
        for a, v in (spacing_override or {}).items():
            if a not in "XYZ" or not math.isfinite(v) or v <= 0:
                raise ImageError("Spacing overrides must be positive finite values in µm for X, Y or Z.")
            calibration[a] = CalibrationValue(value_um=v, source="user confirmed",
                                              candidates=calibration[a].candidates)
            warnings = [w for w in warnings if not w.startswith((f"{a} spacing is missing", f"Conflicting {a} spacing", f"{a} has only generic"))]
        return ImageInfo(filename=path.name, series_index=series_index, series_count=len(tf.series),
                         source_axes=source_axes, axes=axes, shape=list(series.shape),
                         dtype=str(series.dtype), bit_depth=series.dtype.itemsize * 8,
                         dimensions=dims, channel_labels=[labels[i] if i < len(labels) else f"Channel {i+1}" for i in range(dims["C"])],
                         calibration=calibration, warnings=warnings, needs_axis_confirmation=ambiguous,
                         acquisition=acquisition, decoded_bytes=int(math.prod(series.shape) * series.dtype.itemsize))


def read_plane(path: Path, info: ImageInfo, channel: int = 0, z: int = 0, *, tiff=None) -> np.ndarray:
    if info.needs_axis_confirmation:
        raise ImageError("Confirm the axis order before viewing or analyzing this TIFF.")
    if info.dimensions["T"] > 1:
        raise ImageError("Export a single time point before analysis; automatic frame selection is disabled.")
    if not 0 <= channel < info.dimensions["C"] or not 0 <= z < info.dimensions["Z"]:
        raise ImageError("Channel or Z index is outside the image.")
    from contextlib import nullcontext
    with (nullcontext(tiff) if tiff is not None else tifffile.TiffFile(path)) as tf:
        series = tf.series[info.series_index]
        # TIFF pages contain the trailing dimensions; outer dimensions select a page.
        page_shape = series.pages[0].shape
        inner_count = len(page_shape)
        if tuple(series.shape[-inner_count:]) != tuple(page_shape):
            raise ImageError("Unsupported TIFF page layout; no axis is dropped automatically.")
        split = len(info.axes) - inner_count
        coords = {"C": channel, "Z": z, "T": 0}
        outer_shape = series.shape[:split]
        outer_coords = tuple(coords.get(a, 0) for a in info.axes[:split])
        page_index = int(np.ravel_multi_index(outer_coords, outer_shape)) if outer_shape else 0
        arr = series.pages[page_index].asarray()
        inner_axes = info.axes[split:]
        selection = tuple(slice(None) if a in "YX" else coords.get(a, 0) for a in inner_axes)
        arr = arr[selection]
        remaining = "".join(a for a in inner_axes if a in "YX")
        if remaining == "XY":
            arr = arr.T
        if arr.shape != (info.dimensions["Y"], info.dimensions["X"]):
            raise ImageError("The decoded page does not match the confirmed axes.")
        return arr
