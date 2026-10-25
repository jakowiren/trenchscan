"""The line trial on a synthetic scene: cameras on an arc looking at vertical lines whose positions are known."""

import numpy as np
import pytest

from trenchscan.lines import (
    Planes,
    end_heights,
    find_peaks,
    fit_row,
    period,
    profile_along,
    sharpen,
    top_view,
    vertical_direction,
    vertical_rays,
    vertical_segments,
    vote,
)

UP = np.array([0.0, 1.0, 0.0])
LINES_XZ = [(0.0, 0.0), (0.4, 0.0), (0.8, 0.0)]
BOTTOM, TOP = -1.0, 2.0


def synthetic_planes(n_cams: int = 24, seed: int = 0) -> Planes:
    """One segment per line per camera, from BOTTOM to TOP; cameras on an arc in front of the lines."""
    rng = np.random.default_rng(seed)
    C, N, E = [], [], []
    for a in np.linspace(-0.8, 0.8, n_cams):
        cam = np.array([5 * np.sin(a), 0.3 * rng.standard_normal(), -5 * np.cos(a)])
        for x, z in LINES_XZ:
            d = np.stack([np.array([x, BOTTOM, z]) - cam, np.array([x, TOP, z]) - cam])
            n = np.cross(d[0], d[1])
            C.append(cam)
            N.append(n / np.linalg.norm(n))
            E.append(d)
    return Planes(np.array(C), np.array(N), np.array(E))


def true_top_view() -> np.ndarray:
    return np.array([[x, 0.0, z] for x, z in LINES_XZ]) @ top_view(UP).T


def test_top_view_is_orthonormal_and_horizontal():
    up = np.array([0.1, 0.9, -0.2])
    up /= np.linalg.norm(up)
    B = top_view(up)
    assert np.allclose(B @ B.T, np.eye(2))
    assert np.allclose(B @ up, 0)


def test_vertical_direction_recovers_up_despite_clutter():
    planes = synthetic_planes()
    rng = np.random.default_rng(1)
    clutter = rng.standard_normal((len(planes.normals) // 4, 3))
    clutter /= np.linalg.norm(clutter, axis=1, keepdims=True)
    mixed = Planes(np.vstack([planes.centers, planes.centers[: len(clutter)]]),
                   np.vstack([planes.normals, clutter]),
                   np.vstack([planes.ends, planes.ends[: len(clutter)]]))
    tilt = np.radians(8)
    guess = np.array([np.sin(tilt), np.cos(tilt), 0.0])
    up = vertical_direction(mixed, guess)
    assert np.degrees(np.arccos(abs(up @ UP))) < 0.5


def test_vote_puts_a_peak_on_every_line():
    planes = synthetic_planes()
    c, u, keep = vertical_rays(planes, UP)
    assert keep.all()
    truth = true_top_view()
    lo, hi, cell = truth.min(axis=0) - 0.5, truth.max(axis=0) + 0.5, 0.01
    xy, w = find_peaks(sharpen(vote(c, u, lo, hi, cell)), lo, cell)
    strongest = xy[np.argsort(w)[::-1][: len(truth)]]
    for t in truth:
        assert np.linalg.norm(strongest - t, axis=1).min() < 3 * cell


def test_end_heights_and_segments_recover_the_line_ends():
    planes = synthetic_planes()
    c, u, keep = vertical_rays(planes, UP)
    truth = true_top_view()
    h = end_heights(planes, keep, c, u, UP, truth[0])
    assert h.min() == pytest.approx(BOTTOM, abs=1e-6)
    assert h.max() == pytest.approx(TOP, abs=1e-6)
    seg = vertical_segments(planes, keep, c, u, UP, truth, q=0)
    assert seg.shape == (len(truth), 2, 3)
    assert np.allclose(seg[:, :, 1], [[BOTTOM, TOP]] * len(truth), atol=1e-6)


def test_period_finds_the_repeat_distance():
    step = 0.01
    s = np.arange(-1.5, 1.5, step)
    lag, ac = period(1 + np.cos(2 * np.pi * s / 0.36), step, 0.06, 0.5)
    assert lag == pytest.approx(0.36, abs=step)
    assert ac > 0.85   # a perfect repeat still scores (N - lag) / N = 0.88 here, since the overlap shrinks with the lag


def test_profile_along_only_counts_the_band():
    xy = np.array([[0.0, 0.0], [0.5, 0.0], [0.5, 1.0]])   # the last point is off the row
    prof = profile_along(xy, np.ones(3), np.zeros(2), np.array([1.0, 0.0]), half_width=0.1, step=0.25, extent=1.0)
    assert prof.sum() == 2


def test_fit_row_ignores_outliers():
    s = np.linspace(0, 2, 10)
    on = np.c_[s, 0.5 * s]
    xy = np.vstack([on, [[0.0, 2.0], [2.0, -1.0], [1.0, 1.5]]])
    origin, axis, inl = fit_row(xy, np.ones(len(xy)))
    assert inl[:10].all() and not inl[10:].any()
    assert abs(axis @ (np.array([1.0, 0.5]) / np.linalg.norm([1.0, 0.5]))) > 0.999
