"""Capture 1 (2026-10-23): the three clips and the tape-measured ground truth."""

from __future__ import annotations

from pathlib import Path

import yaml

# Clip labels from docs/FINDINGS.md (capture 1), matched by duration.
CLIP_FILES = {
    "clip1": "VID20261023102101.mp4",   # 47 s, top-down, bank cards on the floor
    "clip2": "VID20261023102223.mp4",   # 46 s, side view, then close-up
    "clip3": "VID20261023102419.mp4",   # 36 s, arc from the left end to the front
}


def clips(root: Path) -> dict[str, Path]:
    """Paths of the three clips in data/raw/; raises if any is missing."""
    paths = {name: Path(root) / "data/raw" / f for name, f in CLIP_FILES.items()}
    missing = [p.name for p in paths.values() if not p.exists()]
    if missing:
        raise FileNotFoundError(f"missing in data/raw/: {missing}")
    return paths


def ground_truth(root: Path) -> dict:
    """Tape measurements, from data/ground_truth/radiator_2026-10-23.yaml."""
    return yaml.safe_load((Path(root) / "data/ground_truth/radiator_2026-10-23.yaml").read_text())
