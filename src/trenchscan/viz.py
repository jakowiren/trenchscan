"""3D views of the model: gravity-aligned frame, camera pyramids, interactive plots (notebook 2.3, 3.4)."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from .sfm import Cloud


def gravity_frame(cloud: Cloud) -> np.ndarray:
    """Rotation that makes 'up' = average image-up direction of the cameras.

    Assumes the phone was held roughly upright. Returns R so that R @ x maps world -> (right, up, back).
    """
    R = cloud.cam_rotations
    up = -np.mean([r.T @ np.array([0, 1, 0]) for r in R], axis=0)
    up /= np.linalg.norm(up)
    fwd = np.mean([r.T @ np.array([0, 0, 1]) for r in R], axis=0)
    fwd -= up * (fwd @ up)
    fwd /= np.linalg.norm(fwd)
    return np.stack([np.cross(fwd, up), up, -fwd])


def frustum_lines(cloud: Cloud, size: float) -> np.ndarray:
    """Line segments (NaN-separated) drawing a small pyramid per camera."""
    segs = []
    corners = np.array([(-.56, -1, 1.2), (.56, -1, 1.2), (.56, 1, 1.2), (-.56, 1, 1.2)]) * size
    for R, c in zip(cloud.cam_rotations, cloud.cam_centers):
        k = c + corners @ R  # camera -> world
        for a, b in [(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (2, 3), (3, 4), (4, 1)]:
            p = np.vstack([c, k])
            segs += [p[a], p[b], [np.nan] * 3]
    return np.array(segs)


def plot_cloud(cloud: Cloud, show_cameras: bool = True, point_size: float = 2.0,
               extra: list[go.BaseTraceType] | None = None, title: str = "") -> go.Figure:
    R = gravity_frame(cloud)
    mu = cloud.xyz.mean(axis=0)
    tf = lambda a: (a - mu) @ R.T  # noqa: E731
    p = tf(cloud.xyz)
    # plotly: x right, y depth, z up
    traces = [go.Scatter3d(x=p[:, 0], y=-p[:, 2], z=p[:, 1], mode="markers", name="points",
                           marker=dict(size=point_size, color=[f"rgb({r},{g},{b})" for r, g, b in cloud.rgb.tolist()]))]
    if show_cameras:
        scale = 0.03 * np.ptp(p, axis=0).max()
        f = frustum_lines(cloud, scale)
        f = np.where(np.isnan(f), np.nan, tf(np.nan_to_num(f)))
        traces.append(go.Scatter3d(x=f[:, 0], y=-f[:, 2], z=f[:, 1], mode="lines", name="cameras",
                                   line=dict(color="#E24B4A", width=2)))
    traces += extra or []
    fig = go.Figure(traces)
    fig.update_layout(title=title, height=650, margin=dict(l=0, r=0, t=40, b=0),
                      scene=dict(aspectmode="data", xaxis_visible=False, yaxis_visible=False, zaxis_visible=False))
    return fig


def upright_frame(cloud: Cloud, up: np.ndarray) -> np.ndarray:
    """Like gravity_frame (2.3), but with a given 'up': rows (right, up, back)."""
    back = gravity_frame(cloud)[2]
    back = back - (back @ up) * up
    back /= np.linalg.norm(back)
    return np.stack([np.cross(-back, up), up, back])


def plot_points_and_lines(cloud: Cloud, R: np.ndarray, segments: np.ndarray, title: str = "") -> go.Figure:
    """3D points (grey), camera path (red) and line segments (green) in frame R; plotly z is up."""
    mu = cloud.xyz.mean(axis=0)
    tf = lambda a: (a - mu) @ R.T  # noqa: E731
    p, cam = tf(cloud.xyz), tf(cloud.cam_centers)
    seg = np.concatenate([np.vstack([tf(s), [[np.nan] * 3]]) for s in segments])
    fig = go.Figure([
        go.Scatter3d(x=p[:, 0], y=-p[:, 2], z=p[:, 1], mode="markers", name="3D points (2.2)",
                     marker=dict(size=1.5, color="#AAAAAA")),
        go.Scatter3d(x=cam[:, 0], y=-cam[:, 2], z=cam[:, 1], mode="lines", name="camera path",
                     line=dict(color="#E24B4A", width=3)),
        go.Scatter3d(x=seg[:, 0], y=-seg[:, 2], z=seg[:, 1], mode="lines", name="vertical lines (3.3)",
                     line=dict(color="#1D9E75", width=5)),
    ])
    fig.update_layout(title=title, height=650, margin=dict(l=0, r=0, t=40, b=0),
                      scene=dict(aspectmode="data", xaxis_visible=False, yaxis_visible=False, zaxis_visible=False))
    return fig
