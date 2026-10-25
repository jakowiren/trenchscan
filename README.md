# trenchscan

Weekend prototype: **phone video → 3D reconstruction → recognised components → measurements → documentation**, with an evaluation against tape-measured ground truth.

Test scene: a column radiator in my apartment (vertical tubes ≈ pipes), filmed on a 720p phone (Oppo A38), with bank cards on the floor for scale (not used yet).
Findings so far: [`docs/FINDINGS.md`](docs/FINDINGS.md).
Report: [`report/report.pdf`](report/report.pdf).
Executed notebook with all plots, videos and 3D views: [`notebooks/01_sparse_reconstruction.html`](notebooks/01_sparse_reconstruction.html) (GitHub shows HTML as source: download it and open it in a browser).

## Layout
```
src/trenchscan/    the code, one module per notebook part (video, quality, frames, sfm, viz, points, lines)
tests/             unit tests on synthetic data (pytest; no videos needed)
notebooks/         the notebook: text, plots and run cells, importing src/trenchscan section by section
data/raw/          input videos (git-ignored)
data/ground_truth/ tape measurements (YAML)
outputs/           generated frames / models (git-ignored)
docs/FINDINGS.md   capture log, results, observations
report/            report.md (source), make_figures.py, build.py -> report.pdf (generated, committed as the hand-in)
notebooks/*.html   executed copy of the notebook (generated, committed as the hand-in)
```

The story is **one notebook**, `notebooks/01_sparse_reconstruction.ipynb` (Part 1 looks at the data, Part 2 reconstructs, Part 3 tries line features on the tubes). Its code lives in `src/trenchscan/`, imported section by section.

## Setup
Needs Python ≥ 3.10 and `ffmpeg` on the PATH (`brew install ffmpeg` / `winget install ffmpeg` / `apt install ffmpeg`).
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt   # includes this package (pip install -e .)
nbstripout --install          # strips notebook outputs on commit → clean diffs
# copy the videos into data/raw/ (not in the repo)
jupyter lab notebooks/01_sparse_reconstruction.ipynb
```
Runs on CPU; SfM on ~100 frames at 720p takes about a minute.

Report: after running the notebook once, `python report/make_figures.py && python report/build.py` (needs Google Chrome or Chromium).
Executed notebook: `jupyter nbconvert --to html --execute notebooks/01_sparse_reconstruction.ipynb`.
Checks: `pytest` and `ruff check .`.

## Status
- [x] Frames + blur filter
- [x] Sparse SfM of clip 3 (87/107 frames registered, 0.66 px reprojection error)
- [x] Where the 3D points land: regions without fine detail hold 4 % of them
- [x] Line trial: tube spacing from line segments, 56–58 mm against 55 mm on the tape, without scale
- [ ] Metric scale from the bank cards (clip 1 + clip 3)
- [ ] Cylinder fitting → tube diameter vs 28.6 mm
- [ ] Learned matching / reconstruction (SuperPoint + LightGlue, VGGT / MASt3R) vs SIFT on the tubes
- [ ] Components and CAD export
