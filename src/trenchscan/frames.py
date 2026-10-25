"""Frame extraction and the blur filter (notebook 2.1)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np


def extract_frames(video: Path, out_dir: Path, fps: float = 4.0) -> list[Path]:
    """Extract frames with ffmpeg (respects the phone's rotation metadata)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(video),
         "-vf", f"fps={fps}", "-q:v", "2", str(out_dir / "%04d.jpg")],
        check=True,
    )
    return sorted(out_dir.glob("*.jpg"))


def sharpness(path: Path) -> float:
    """Variance of the Laplacian: low = blurry."""
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    return float(cv2.Laplacian(img, cv2.CV_64F).var())


def filter_sharp(frames: list[Path], out_dir: Path, keep_fraction: float = 0.75) -> tuple[list[Path], np.ndarray]:
    """Copy the sharpest `keep_fraction` of frames to out_dir. Returns kept paths and all scores."""
    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    scores = np.array([sharpness(f) for f in frames])
    threshold = np.percentile(scores, 100 * (1 - keep_fraction))
    kept = []
    for f, s in zip(frames, scores):
        if s >= threshold:
            kept.append(Path(shutil.copy(f, out_dir)))
    return kept, scores
