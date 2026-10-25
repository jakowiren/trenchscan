# trenchscan

Weekend prototype: **phone video → 3D reconstruction → recognised components → measurements → documentation**, with an evaluation against tape-measured ground truth.

Test scene: a column radiator in my apartment (vertical tubes ≈ pipes), filmed on a 720p phone with a bank card for scale.
Findings so far: [`docs/FINDINGS.md`](docs/FINDINGS.md).

## Layout
```
notebooks/         all code for now: each step = a definitions cell + a run cell
data/raw/          input videos (git-ignored)
data/ground_truth/ tape measurements (YAML)
outputs/           generated frames / models (git-ignored)
docs/FINDINGS.md   capture log, results, observations
```

Exploration phase: all code lives in **one notebook**, `notebooks/01_sparse_reconstruction.ipynb`, next to its plots (Part 1 looks at the data, Part 2 reconstructs, Part 3 tries line features on the tubes). Once a step stabilises, its definitions cell moves to `src/trenchscan/` and the notebook imports it.

## Setup
Needs Python ≥ 3.10 and `ffmpeg` on the PATH (`brew install ffmpeg` / `winget install ffmpeg` / `apt install ffmpeg`).
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
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
