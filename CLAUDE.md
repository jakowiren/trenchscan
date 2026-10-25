# trenchscan: how we work

What the project is and how to run it: `README.md`. Results so far: `docs/FINDINGS.md`. This file only holds working rules.

## One notebook, one package
- The story lives in `notebooks/01_sparse_reconstruction.ipynb`, top to bottom in parts (Part 1 look at the data, Part 2 sparse reconstruction, Part 3 line trial, next Part 4 scale). A new step becomes a new part or section there, never a new notebook. (decided 2026-10-25)
- The code lives in `src/trenchscan/`, one module per part (`video`, `quality`, `frames`, `sfm`, `viz`, `points`, `lines`). Each notebook section has one `# --- definitions: ... (src/trenchscan/x.py) ---` import cell, then its run cells. New exploratory code may start as functions in a notebook cell; once it works it moves into the package with a test, so the notebook stays text, plots and run cells. (decided 2026-10-25)
- Checks before every commit: `pytest` (unit tests on synthetic data, no videos needed) and `ruff check .` (also lints the notebook). Fix every error first.

## Editing the notebook while the user has it open
- The user runs the notebook in Jupyter Lab; Claude edits the `.ipynb` on disk. Claude edits only after the user has saved (Ctrl+S), and the user then reloads (File > Reload Notebook from Disk, or "Revert" in the file-changed dialog, never "Overwrite").
- Claude test-runs a change headless on a copy outside the repo before writing the real file.

## One place per fact
- The notebook reads top to bottom: each cell follows from the ones above and leads to the next. A cell may point back ("as 1.3 showed") but never forward to a later part or its results; code a part needs is defined in that part, not in setup. (decided 2026-10-25)
- What a plot shows is written right below it in the notebook, as observations rather than questions (decided 2026-10-25).
- Hand-ins are the repo, the notebook and the PDF report (a school-style assignment: learn the concepts, discuss them). The notebook holds the evidence; `report/report.md` holds the argument (theory, findings, discussion against sizeless, future work), brief and citing notebook sections like §2.4. Every number in the report must be printed by `report/make_figures.py`, which uses the same package functions as the notebook, so report and notebook cannot drift apart.
- `report/report.md` is written in Jakob's speaking voice, like an academic-style oral presentation, in story order: "I looked at Figure A, saw X, so I tried Y". "I" for what was done, "our" is fine in the discussion. Plain words and connectors (so, since, because); no semicolon-and-negation punchlines, colon reveals or stock formal phrases. Theory talks about the people filming, not only "the camera". When unsure whether a passage sounds like Jakob, ask him with options instead of guessing. (decided 2026-10-25)
- Graphs carry the argument: a figure that shows a finding beats a paragraph describing it. More pages of figures that each show something are fine; word soup is not.
- `docs/FINDINGS.md` is the dated capture log. Rewrite a line when it goes stale; don't append a contradiction.
- Generated files (frames, models, video previews) go in `outputs/`: git-ignored, reproducible from the notebook. Raw videos stay in `data/raw/`, also git-ignored. The generated files in git are the hand-ins `report/report.pdf` and `notebooks/01_sparse_reconstruction.html`: rebuild them (`python report/make_figures.py && python report/build.py`; `jupyter nbconvert --to html --execute notebooks/01_sparse_reconstruction.ipynb`) in the same commit as any change to the notebook, the package or `report.md`, so they never show an older state.
- nbstripout strips outputs on commit, so embedded previews and plots never reach git.
- Third-party images (for example sizeless.co product shots) are linked by URL with credit, never copied into the repo: it may go public. Own images (frames from our clips) are embedded as notebook attachments.
