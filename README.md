# trenchscan

Weekend prototype: **phone video → 3D reconstruction → recognised components → measurements → documentation**, with an evaluation against tape-measured ground truth.

Test scene: a column radiator in my apartment (vertical tubes ≈ pipes), filmed on a 720p phone with a bank card for scale.
Findings so far: [`docs/FINDINGS.md`](docs/FINDINGS.md).

## Layout
```
src/trenchscan/    pipeline code (importable package)
  frames.py        frame extraction + blur filter
  sfm.py           structure-from-motion (pycolmap) + point-cloud helpers
  viz.py           interactive 3D plots (plotly)
notebooks/         exploration & visualisation — call the package, hold no core logic
data/raw/          input videos (git-ignored)
data/ground_truth/ tape measurements (YAML)
outputs/           generated frames / models (git-ignored)
docs/FINDINGS.md   capture log, results, observations
```

## Setup
Needs Python ≥ 3.10 and `ffmpeg` on the PATH (`brew install ffmpeg` / `winget install ffmpeg` / `apt install ffmpeg`).
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
nbstripout --install          # strips notebook outputs on commit → clean diffs
# copy the videos into data/raw/
jupyter lab notebooks/01_sparse_reconstruction.ipynb
```
Runs on CPU; SfM on ~100 frames at 720p takes about a minute.

## Status
- [x] Frames + blur filter
- [x] Sparse SfM (87/107 frames registered, 0.67 px reprojection error)
- [ ] Metric scale from bank card
- [ ] Tube segmentation (SAM 2) → 3D labels
- [ ] Cylinder fitting → diameter / spacing vs ground truth
- [ ] Agent report + DXF export
- [ ] Learned reconstruction (VGGT / MASt3R) vs SIFT on textureless tubes
