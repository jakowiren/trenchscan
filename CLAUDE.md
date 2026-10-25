# trenchscan: how we work

What the project is and how to run it: `README.md`. Results so far: `docs/FINDINGS.md`. This file only holds working rules.

## One notebook
- All exploration code lives in `notebooks/01_sparse_reconstruction.ipynb`, top to bottom in parts (Part 1 look at the data, Part 2 sparse reconstruction, Part 3 line trial, next Part 4 scale). A new step becomes a new part or section there, never a new notebook. (decided 2026-10-25)
- Each step is a definitions cell plus a run cell. When a step stabilises, its definitions move to `src/trenchscan/` and the notebook imports them, so the notebook shrinks instead of only growing.

## Editing the notebook while the user has it open
- The user runs the notebook in Jupyter Lab; Claude edits the `.ipynb` on disk. Claude edits only after the user has saved (Ctrl+S), and the user then reloads (File > Reload Notebook from Disk, or "Revert" in the file-changed dialog, never "Overwrite").
- Claude test-runs a change headless on a copy outside the repo before writing the real file.

## One place per fact
- The notebook reads top to bottom: each cell follows from the ones above and leads to the next. A cell may point back ("as 1.3 showed") but never forward to a later part or its results; code a part needs is defined in that part, not in setup. (decided 2026-10-25)
- What a plot shows is written right below it in the notebook, as observations rather than questions (decided 2026-10-25).
- Hand-ins are the repo, the notebook and the PDF report (a school-style assignment: learn the concepts, discuss them). The notebook holds the evidence; `report/report.md` holds the argument (theory, findings, discussion against sizeless, future work), brief and citing notebook sections like §2.4. Every number in the report must be printed by `report/make_figures.py`, which runs the notebook's own definition cells, so report and notebook cannot drift apart.
- `docs/FINDINGS.md` is the dated capture log. Rewrite a line when it goes stale; don't append a contradiction.
- Generated files (frames, models, video previews) go in `outputs/`: git-ignored, reproducible from the notebook. Raw videos stay in `data/raw/`, also git-ignored. The one generated file in git is `report/report.pdf`, the hand-in: rebuild it (`python report/make_figures.py && python report/build.py`) in the same commit as any change to `report.md` or the notebook numbers it quotes.
- nbstripout strips outputs on commit, so embedded previews and plots never reach git.
- Third-party images (for example sizeless.co product shots) are linked by URL with credit, never copied into the repo: it may go public. Own images (frames from our clips) are embedded as notebook attachments.
