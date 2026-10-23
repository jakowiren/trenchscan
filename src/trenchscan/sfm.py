"""Structure-from-motion with pycolmap (CPU-friendly defaults)."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pycolmap


def run_sfm(image_dir: Path, out_dir: Path, max_features: int = 4000, overlap: int = 12,
            overwrite: bool = False) -> pycolmap.Reconstruction:
    """SIFT features -> sequential matching -> incremental mapping. Returns the largest model.

    Results are cached in out_dir; pass overwrite=True to recompute.
    """
    image_dir, out_dir = Path(image_dir), Path(out_dir)
    model_dir = out_dir / "0"
    if model_dir.exists() and not overwrite:
        return pycolmap.Reconstruction(model_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    db = out_dir / "database.db"

    extraction = pycolmap.FeatureExtractionOptions()
    extraction.sift.max_num_features = max_features
    pycolmap.extract_features(db, image_dir, camera_mode=pycolmap.CameraMode.SINGLE,
                              extraction_options=extraction, device=pycolmap.Device.cpu)

    pairing = pycolmap.SequentialPairingOptions()
    pairing.overlap = overlap
    pairing.loop_detection = False
    pycolmap.match_sequential(db, pairing_options=pairing, device=pycolmap.Device.cpu)

    models = pycolmap.incremental_mapping(db, image_dir, out_dir)
    if not models:
        raise RuntimeError("No model could be reconstructed")
    best = max(models, key=lambda k: models[k].num_reg_images())
    if best != 0:  # keep the largest model at out_dir/0 for caching
        shutil.rmtree(model_dir, ignore_errors=True)
        (out_dir / str(best)).rename(model_dir)
    return pycolmap.Reconstruction(model_dir)


@dataclass
class Cloud:
    xyz: np.ndarray        # (N, 3) points
    rgb: np.ndarray        # (N, 3) uint8 colours
    error: np.ndarray      # (N,) reprojection error, px
    track: np.ndarray      # (N,) number of images observing each point
    cam_centers: np.ndarray  # (M, 3) camera centres, in frame order
    cam_rotations: np.ndarray  # (M, 3, 3) world-to-camera rotations
    names: list[str]


def to_cloud(rec: pycolmap.Reconstruction) -> Cloud:
    pts = list(rec.points3D.values())
    ims = sorted(rec.images.values(), key=lambda im: im.name)
    return Cloud(
        xyz=np.array([p.xyz for p in pts]),
        rgb=np.array([p.color for p in pts], dtype=np.uint8),
        error=np.array([p.error for p in pts]),
        track=np.array([p.track.length() for p in pts]),
        cam_centers=np.array([im.projection_center() for im in ims]),
        cam_rotations=np.array([im.cam_from_world().rotation.matrix() for im in ims]),
        names=[im.name for im in ims],
    )


def clean(cloud: Cloud, max_error: float = 1.5, min_track: int = 3, keep_percentile: float = 97) -> Cloud:
    """Drop high-error / short-track points and far outliers."""
    m = (cloud.error < max_error) & (cloud.track >= min_track)
    xyz = cloud.xyz[m]
    d = np.linalg.norm(xyz - np.median(xyz, axis=0), axis=1)
    m2 = d < np.percentile(d, keep_percentile)
    idx = np.flatnonzero(m)[m2]
    return Cloud(cloud.xyz[idx], cloud.rgb[idx], cloud.error[idx], cloud.track[idx],
                 cloud.cam_centers, cloud.cam_rotations, cloud.names)


def summary(rec: pycolmap.Reconstruction, n_input: int) -> dict:
    return {
        "input_frames": n_input,
        "registered": rec.num_reg_images(),
        "registered_pct": round(100 * rec.num_reg_images() / n_input, 1),
        "points": rec.num_points3D(),
        "mean_reproj_error_px": round(rec.compute_mean_reprojection_error(), 3),
        "mean_track_length": round(rec.compute_mean_track_length(), 2),
    }
