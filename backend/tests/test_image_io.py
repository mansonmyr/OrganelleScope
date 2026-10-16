from pathlib import Path

import numpy as np
import pytest
import tifffile

from organelle_scope.image_io import ImageError, inspect_tiff, read_plane


def test_ome_stack_retains_all_channels_and_planes(tmp_path: Path):
    a = np.arange(3 * 4 * 8 * 9, dtype=np.uint16).reshape(3, 4, 8, 9)
    path = tmp_path / "stack.ome.tiff"
    tifffile.imwrite(path, a, ome=True, photometric="minisblack", metadata={
        "axes": "ZCYX", "PhysicalSizeX": 65., "PhysicalSizeXUnit": "nm",
        "PhysicalSizeY": .08, "PhysicalSizeZ": .3,
        "Channel": {"Name": ["Protein X", "Pericentrin", "MitoTracker", "DAPI"]}})
    info = inspect_tiff(path)
    assert info.dtype == "uint16" and info.bit_depth == 16
    assert info.dimensions == {"T": 1, "C": 4, "Z": 3, "Y": 8, "X": 9}
    assert info.calibration["X"].value_um == pytest.approx(.065)
    assert info.calibration["Y"].value_um == .08
    assert info.channel_labels[2] == "MitoTracker"
    for z in range(3):
        for c in range(4):
            np.testing.assert_array_equal(read_plane(path, info, c, z), a[z, c])


def test_imagej_resolution_and_spacing(tmp_path):
    path = tmp_path / "ij.tif"
    a = np.zeros((5, 2, 8, 9), dtype=np.uint16)
    tifffile.imwrite(path, a, imagej=True, resolution=(10, 5), metadata={
        "axes": "ZCYX", "spacing": .4, "unit": "um"})
    info = inspect_tiff(path)
    assert [info.calibration[a].value_um for a in "XYZ"] == [.1, .2, .4]


def test_ambiguous_pages_require_confirmation(tmp_path):
    path = tmp_path / "ambiguous.tif"
    a = np.arange(3 * 8 * 9, dtype=np.uint16).reshape(3, 8, 9)
    tifffile.imwrite(path, a, photometric="minisblack", metadata=None)
    info = inspect_tiff(path)
    assert info.needs_axis_confirmation
    with pytest.raises(ImageError, match="Confirm"):
        read_plane(path, info)
    corrected = inspect_tiff(path, axes_override="ZYX")
    np.testing.assert_array_equal(read_plane(path, corrected, z=2), a[2])


def test_rgb_is_not_silently_treated_as_scientific_channels(tmp_path):
    path = tmp_path / "rgb.tif"
    a = np.arange(8 * 9 * 3, dtype=np.uint8).reshape(8, 9, 3)
    tifffile.imwrite(path, a, photometric="rgb")
    assert inspect_tiff(path).needs_axis_confirmation
    info = inspect_tiff(path, axes_override="YXC")
    np.testing.assert_array_equal(read_plane(path, info, channel=2), a[..., 2])


def test_conflicting_metadata_needs_user_override(tmp_path):
    path = tmp_path / "conflict.ome.tif"
    tifffile.imwrite(path, np.zeros((8, 9), np.uint16), ome=True, resolution=(10000, 10000),
                       resolutionunit="CENTIMETER", metadata={"PhysicalSizeX": .1, "PhysicalSizeY": .1})
    info = inspect_tiff(path)
    assert info.calibration["X"].conflict and not info.calibrated()
    fixed = inspect_tiff(path, spacing_override={"X": .1, "Y": .1})
    assert fixed.calibrated() and fixed.calibration["X"].source == "user confirmed"
    assert len(fixed.calibration["X"].candidates) == 2


def test_no_default_physical_scale_and_no_time_selection(tmp_path):
    path = tmp_path / "time.ome.tif"
    tifffile.imwrite(path, np.zeros((2, 8, 9), np.uint16), ome=True, photometric="minisblack", metadata={"axes": "TYX"})
    info = inspect_tiff(path)
    assert not info.calibrated()
    with pytest.raises(ImageError, match="single time point"):
        read_plane(path, info)


@pytest.mark.parametrize("dtype", [np.float32, np.int16, np.uint32])
def test_invalid_pixel_types_rejected(tmp_path, dtype):
    path = tmp_path / "invalid.tif"
    tifffile.imwrite(path, np.zeros((8, 9), dtype))
    with pytest.raises(ImageError, match="uint8 or uint16"):
        inspect_tiff(path)


def test_bad_overrides_rejected(tmp_path):
    path = tmp_path / "plain.tif"
    tifffile.imwrite(path, np.zeros((8, 9), np.uint16))
    with pytest.raises(ImageError):
        inspect_tiff(path, axes_override="YY")
    with pytest.raises(ImageError):
        inspect_tiff(path, spacing_override={"X": float("nan")})


def test_channel_first_storage_and_bounds(tmp_path):
    path = tmp_path / "channels.tif"
    a = np.arange(4 * 3 * 8 * 9, dtype=np.uint16).reshape(4, 3, 8, 9)
    tifffile.imwrite(path, a, photometric="minisblack", metadata={"axes": "CZYX"})
    info = inspect_tiff(path)
    np.testing.assert_array_equal(read_plane(path, info, channel=3, z=2), a[3, 2])
    with pytest.raises(ImageError):
        read_plane(path, info, channel=4)
