"""Smaller pieces: frame times, the smooth-region mask, the blur filter, point-cloud cleaning, clip lookup."""

import cv2
import numpy as np
import pytest

from trenchscan.capture import clips
from trenchscan.frames import filter_sharp, sharpness
from trenchscan.points import frame_time, smooth_mask
from trenchscan.sfm import Cloud, clean


def test_frame_time_from_ffmpeg_numbering():
    assert frame_time("0001.jpg") == 0.0
    assert frame_time("outputs/clip3/frames/0009.jpg", fps=4) == 2.0


def test_smooth_mask_counts_shading_as_smooth_and_texture_as_not():
    ramp = np.tile(np.linspace(0, 255, 200), (100, 1)).astype(np.uint8)    # soft shading, like a tube face
    noise = np.random.default_rng(0).integers(0, 255, (100, 200)).astype(np.uint8)
    assert smooth_mask(ramp)[10:-10, 10:-10].mean() > 0.95
    assert smooth_mask(noise).mean() < 0.05


def test_filter_sharp_keeps_the_sharp_frames(tmp_path):
    board = (np.indices((120, 160)).sum(axis=0) // 8 % 2 * 255).astype(np.uint8)
    paths = []
    for i, img in enumerate([board, cv2.GaussianBlur(board, (0, 0), 4), board, cv2.GaussianBlur(board, (0, 0), 4)]):
        p = tmp_path / f"{i + 1:04d}.jpg"
        cv2.imwrite(str(p), img)
        paths.append(p)
    assert sharpness(paths[0]) > sharpness(paths[1])
    kept, scores = filter_sharp(paths, tmp_path / "kept", keep_fraction=0.5)
    assert [p.name for p in kept] == ["0001.jpg", "0003.jpg"]
    assert len(scores) == 4


def test_clean_drops_bad_and_far_points():
    rng = np.random.default_rng(0)
    xyz = np.vstack([rng.normal(0, 1, (100, 3)), [[50.0, 50.0, 50.0]]])
    error = np.full(101, 0.5)
    error[0] = 3.0                      # too large a reprojection error
    track = np.full(101, 5)
    track[1] = 2                        # seen in too few frames
    cloud = Cloud(xyz, np.zeros((101, 3), np.uint8), error, track, np.zeros((1, 3)), np.eye(3)[None], ["a"])
    out = clean(cloud)
    kept = {tuple(p) for p in out.xyz}
    assert tuple(xyz[0]) not in kept and tuple(xyz[1]) not in kept and (50.0, 50.0, 50.0) not in kept
    assert 90 < len(out.xyz) < 99


def test_clips_reports_missing_videos(tmp_path):
    with pytest.raises(FileNotFoundError, match="missing in data/raw"):
        clips(tmp_path)
