"""Where the 3D points land in the frames, against regions without fine detail (notebook 2.4)."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pycolmap


def frame_time(name: str, fps: float = 4.0) -> float:
    """Time in the clip of an extracted frame; ffmpeg numbers them 0001, 0002, ... at `fps`."""
    return (int(Path(name).stem) - 1) / fps


def smooth_mask(grey: np.ndarray, sigma: float = 2.0, win: int = 15, thr: float = 1.5) -> np.ndarray:
    """True where the image has no fine detail: mean |image - Gaussian blur(sigma)| over win x win pixels below `thr` grey levels.

    Smooth shading counts as smooth (a gradient-based test would miss the shaded tube faces); edges and texture do not.
    SIFT looks for small-scale blobs and corners, so it finds almost nothing in these regions.
    """
    g = grey.astype(np.float32)
    detail = np.abs(g - cv2.GaussianBlur(g, (0, 0), sigma))
    return cv2.blur(detail, (win, win)) < thr


def point_pixels(im: pycolmap.Image) -> np.ndarray:
    """(N, 2) pixel positions of the keypoints in this image that became 3D points."""
    return np.array([p.xy for p in im.points2D if p.has_point3D()]).reshape(-1, 2)


def smooth_share(rec: pycolmap.Reconstruction, image_dir: Path, thr: float = 1.5) -> tuple[float, float]:
    """(% of image area that is smooth, % of 3D-point observations inside it), over all registered frames."""
    area, inside, total = [], 0, 0
    for im in rec.images.values():
        m = smooth_mask(cv2.imread(str(Path(image_dir) / im.name), cv2.IMREAD_GRAYSCALE), thr=thr)
        xy = np.clip(point_pixels(im).astype(int), 0, [m.shape[1] - 1, m.shape[0] - 1])
        area.append(m.mean())
        inside += m[xy[:, 1], xy[:, 0]].sum()
        total += len(xy)
    return 100 * float(np.mean(area)), 100 * inside / total
