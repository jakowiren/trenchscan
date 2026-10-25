"""Per-frame quality over a clip, and SIFT keypoints on single frames (notebook 1.3, 1.4)."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def frame_stats(video: Path, step: int = 3, flow_width: int = 320) -> dict[str, np.ndarray]:
    """Per sampled frame (every `step`-th): time and four quality measures.

    sharpness   variance of the Laplacian, full-res grey
    brightness  mean grey level, 0-255
    clipped     fraction of pixels <= 5 or >= 250 (crushed shadows / blown highlights)
    motion      median optical-flow speed since the previous sample, full-res px per second
    """
    cap = cv2.VideoCapture(str(video))
    rows, prev, prev_t, i = [], None, None, 0
    while True:
        if i % step:
            if not cap.grab():
                break
            i += 1
            continue
        ok, bgr = cap.read()
        if not ok:
            break
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        scale = flow_width / grey.shape[1]
        small = cv2.resize(grey, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        motion = np.nan
        if prev is not None and t > prev_t:
            flow = cv2.calcOpticalFlowFarneback(prev, small, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            motion = np.median(np.linalg.norm(flow, axis=2)) / scale / (t - prev_t)
        rows.append((t, cv2.Laplacian(grey, cv2.CV_64F).var(), grey.mean(),
                     np.mean((grey <= 5) | (grey >= 250)), motion))
        prev, prev_t = small, t
        i += 1
    cap.release()
    return dict(zip(["t", "sharpness", "brightness", "clipped", "motion"], np.array(rows).T))


def sift_keypoints(rgb: np.ndarray, max_features: int = 4000) -> np.ndarray:
    """(N, 2) SIFT keypoint positions in pixels."""
    grey = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    kps = cv2.SIFT_create(nfeatures=max_features).detect(grey, None)
    return np.array([k.pt for k in kps]).reshape(-1, 2)
