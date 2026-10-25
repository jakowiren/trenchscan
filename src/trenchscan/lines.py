"""Line segments instead of points: vertical lines found by voting from above (notebook Part 3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import pycolmap

_LSD = cv2.createLineSegmentDetector()


def detect_lines(grey: np.ndarray, min_len: float = 40.0) -> np.ndarray:
    """(N, 4) line segments x1, y1, x2, y2 found by LSD, at least min_len pixels long."""
    seg = _LSD.detect(grey)[0]
    seg = np.zeros((0, 4)) if seg is None else seg.reshape(-1, 4)
    return seg[np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1]) >= min_len]


@dataclass
class Planes:
    centers: np.ndarray  # (N, 3) camera centre of the frame each segment was seen in
    normals: np.ndarray  # (N, 3) unit normal of the plane through that centre and the segment
    ends: np.ndarray     # (N, 2, 3) viewing directions of the segment's two end points, world frame


def segment_planes(rec: pycolmap.Reconstruction, image_dir: Path, min_len: float = 40.0) -> Planes:
    """Detect segments in every registered frame and turn each into a plane in the model's world frame."""
    C, N, E = [], [], []
    for im in sorted(rec.images.values(), key=lambda im: im.name):
        K_inv = np.linalg.inv(rec.cameras[im.camera_id].calibration_matrix())
        R = im.cam_from_world().rotation.matrix()
        grey = cv2.imread(str(Path(image_dir) / im.name), cv2.IMREAD_GRAYSCALE)
        for x1, y1, x2, y2 in detect_lines(grey, min_len):
            d = (R.T @ K_inv @ np.array([[x1, x2], [y1, y2], [1.0, 1.0]])).T   # viewing directions of both ends
            n = np.cross(d[0], d[1])
            C.append(im.projection_center())
            N.append(n / np.linalg.norm(n))
            E.append(d)
    return Planes(np.array(C), np.array(N), np.array(E))


def vertical_direction(planes: Planes, guess: np.ndarray, max_deg=(10, 5, 5)) -> np.ndarray:
    """The direction most segment planes contain.

    A plane contains direction v when its normal is perpendicular to v, so v is the direction most perpendicular
    to the normals (their smallest singular vector), refit on the planes within max_deg of containing it.
    """
    v = guess / np.linalg.norm(guess)
    for deg in max_deg:
        near = np.abs(planes.normals @ v) < np.sin(np.radians(deg))
        v = np.linalg.svd(planes.normals[near])[2][-1]
        v *= np.sign(v @ guess)
    return v


def top_view(up: np.ndarray) -> np.ndarray:
    """(2, 3) matrix: world point -> 2D coordinates seen from above, i.e. perpendicular to `up`."""
    e1 = np.cross(up, [1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)
    return np.stack([e1, np.cross(up, e1)])


def vertical_rays(planes: Planes, up: np.ndarray, max_deg: float = 3.0):
    """Top-view rays (start c, unit direction u) of the segments whose plane contains the vertical within max_deg,
    and the mask of which segments those are. Seen from above, such a plane is a ray from the camera."""
    keep = np.abs(planes.normals @ up) < np.sin(np.radians(max_deg))
    B = top_view(up)
    c = planes.centers[keep] @ B.T
    n = planes.normals[keep] @ B.T
    u = np.c_[-n[:, 1], n[:, 0]]
    u /= np.linalg.norm(u, axis=1, keepdims=True)
    look = planes.ends[keep].mean(axis=1) @ B.T
    u *= np.sign(np.sum(u * look, axis=1))[:, None]   # point each ray the way its camera looks
    return c, u, keep


def vote(c: np.ndarray, u: np.ndarray, lo: np.ndarray, hi: np.ndarray, cell: float) -> np.ndarray:
    """Hough-style vote: every ray adds 1 to each grid cell it crosses. Rows run along the second top-view axis."""
    nx, ny = np.ceil((hi - lo) / cell).astype(int)
    votes = np.zeros((ny, nx))
    corners = np.array([lo, hi, [lo[0], hi[1]], [hi[0], lo[1]]])
    reach = np.linalg.norm(c[:, None] - corners[None], axis=2).max()
    lam = np.arange(0, reach, cell / 2)
    for ci, ui in zip(c, u):
        ij = np.floor((ci + lam[:, None] * ui - lo) / cell).astype(int)
        ij = np.unique(ij[(ij >= 0).all(axis=1) & (ij[:, 0] < nx) & (ij[:, 1] < ny)], axis=0)
        votes[ij[:, 1], ij[:, 0]] += 1
    return votes


def sharpen(votes: np.ndarray, fine: float = 1.5, coarse: float = 8.0) -> np.ndarray:
    """Difference of Gaussians (sigmas in grid cells): keeps compact crossings, removes the broad haze."""
    return cv2.GaussianBlur(votes, (0, 0), fine) - cv2.GaussianBlur(votes, (0, 0), coarse)


def find_peaks(img: np.ndarray, lo: np.ndarray, cell: float, pct: float = 99.5, win: int = 9):
    """Local maxima above the pct-th percentile: (N, 2) top-view positions and (N,) strengths."""
    ij = np.argwhere((img == cv2.dilate(img, np.ones((win, win)))) & (img > np.percentile(img, pct)))
    return lo + (ij[:, ::-1] + 0.5) * cell, img[ij[:, 0], ij[:, 1]]


def fit_row(xy: np.ndarray, w: np.ndarray, tol: float = 0.1):
    """Straight line through the most peak strength (every pair of peaks tried), refit by weighted PCA of its inliers.

    Returns (origin, unit direction, inlier mask).
    """
    best_score, best = -1.0, None
    for i in range(len(xy)):
        for j in range(i + 1, len(xy)):
            a = (xy[j] - xy[i]) / np.linalg.norm(xy[j] - xy[i])
            inl = np.abs((xy - xy[i]) @ np.array([a[1], -a[0]])) < tol
            if w[inl].sum() > best_score:
                best_score, best = w[inl].sum(), inl
    o = np.average(xy[best], axis=0, weights=w[best])
    a = np.linalg.svd((xy[best] - o) * np.sqrt(w[best])[:, None])[2][0]
    return o, a, best


def profile_along(xy: np.ndarray, w: np.ndarray, origin, axis, half_width: float, step: float, extent: float) -> np.ndarray:
    """Weights w of 2D positions xy within half_width of the row, summed in bins of `step` along it."""
    s = (xy - origin) @ axis
    near = np.abs((xy - origin) @ np.array([axis[1], -axis[0]])) < half_width
    return np.histogram(s[near], np.arange(-extent, extent + step, step), weights=w[near])[0]


def period(profile: np.ndarray, step: float, min_lag: float, max_lag: float) -> tuple[float, float]:
    """Strongest repeat distance of a profile: the lag of highest autocorrelation between min_lag and max_lag.

    Returns (lag, autocorrelation there: 1 = a perfect repeat, 0 = none).
    """
    p = profile - profile.mean()
    ac = np.correlate(p, p, "full")[len(p) - 1:] / (p @ p)
    lag = np.arange(len(ac)) * step
    k = np.argmax(np.where((lag >= min_lag) & (lag <= max_lag), ac, -np.inf))
    return float(lag[k]), float(ac[k])


def end_heights(planes: Planes, keep, c, u, up, x0, tol: float = 0.015) -> np.ndarray:
    """Heights along `up` of the end points of the segments whose top-view ray passes within tol of x0."""
    rel = x0 - c
    hit = (np.sum(rel * u, axis=1) > 0) & (np.abs(rel[:, 0] * u[:, 1] - rel[:, 1] * u[:, 0]) < tol)
    B = top_view(up)
    ends = planes.ends[keep][hit]                     # (M, 2, 3)
    d2 = ends @ B.T                                   # their directions seen from above
    mu = np.einsum("mk,mjk->mj", rel[hit], d2) / np.einsum("mjk,mjk->mj", d2, d2)
    return ((planes.centers[keep][hit][:, None] + mu[..., None] * ends) @ up).ravel()


def vertical_segments(planes: Planes, keep, c, u, up, peaks: np.ndarray, q: float = 2.0) -> np.ndarray:
    """(M, 2, 3) world end points of one vertical line per top-view peak, from the q-th to the (100-q)-th
    percentile of the heights where its supporting segments end."""
    B = top_view(up)
    out = []
    for x0 in peaks:
        bottom, top = np.percentile(end_heights(planes, keep, c, u, up, x0), [q, 100 - q])
        base = B.T @ x0                      # the peak's position, at height 0
        out.append([base + bottom * up, base + top * up])
    return np.array(out)
