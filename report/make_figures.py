"""Figures and key numbers for report.md, from the notebook's own code and its cached outputs.

Run from the repo root after running the notebook once (it needs outputs/clip3/):
    python report/make_figures.py

The notebook stays the single source of the analysis code: this script executes its setup cell and every
cell that starts with "# --- definitions:", then redraws the plots the report needs as static PNGs in
report/figures/ and prints the numbers the report quotes, so they can be checked against report.md.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/01_sparse_reconstruction.ipynb"
OUT = ROOT / "report/figures"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def load_notebook_code() -> dict:
    cells = [c for c in json.loads(NOTEBOOK.read_text())["cells"] if c["cell_type"] == "code"]
    src = ["".join(c["source"]) for c in cells]
    setup = next(s for s in src if "CLIPS = {" in s)
    module = types.ModuleType("notebook")   # a real module, so the notebook's dataclasses work
    sys.modules["notebook"] = module
    ns = module.__dict__
    root_expr = 'Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()'
    assert root_expr in setup, "setup cell no longer sets ROOT the expected way"
    exec(setup.replace(root_expr, f"Path({str(ROOT)!r})"), ns)
    for s in src:
        if s.startswith("# --- definitions:"):
            exec(s, ns)
    return ns


def main() -> None:
    nb = load_notebook_code()
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("fig*"):   # figures are regenerated each run; drop ones the report no longer uses
        old.unlink()
    CLIPS, cv2, pycolmap = nb["CLIPS"], nb["cv2"], nb["pycolmap"]
    work = ROOT / "outputs/clip3"
    rec = pycolmap.Reconstruction(work / "sparse/0")
    frame_time = nb["frame_time"]

    # Fig 1: the scene, one frame per clip (clip 1 cropped to leave out the feet)
    tiles = []
    for name, t, keep in [("clip1", 2.0, 0.72), ("clip2", 9.6, 1.0), ("clip3", 19.4, 1.0)]:
        f = nb["read_at"](CLIPS[name], [t])[0]
        f = f[:, : round(f.shape[1] * keep)]
        tiles.append(cv2.resize(f, (round(f.shape[1] * 320 / f.shape[0]), 320)))
    gap = np.full((320, 8, 3), 255, np.uint8)
    strip = np.hstack([tiles[0], gap, tiles[1], gap, tiles[2]])
    plt.imsave(OUT / "fig1_scene.jpg", strip)

    # sharpness and image speed per clip (the plot itself lives in notebook 1.3)
    stats = {name: nb["frame_stats"](path) for name, path in CLIPS.items()}

    # Fig 2: smooth regions and 3D points (top), line segments (bottom), on the same three frames
    ims = sorted(rec.images.values(), key=lambda im: frame_time(im.name))
    fig, ax = plt.subplots(2, 3, figsize=(5.6, 6.6))
    for k, target in enumerate((3, 15, 27)):
        im = min(ims, key=lambda im: abs(frame_time(im.name) - target))
        grey = cv2.imread(str(work / "frames" / im.name), cv2.IMREAD_GRAYSCALE)
        m = nb["smooth_mask"](grey)
        xy = nb["point_pixels"](im)
        seg = nb["detect_lines"](grey)
        top, bottom = ax[0, k], ax[1, k]
        top.imshow(grey, cmap="gray"); top.imshow(np.ma.masked_where(~m, m), cmap="winter", alpha=0.45)
        top.scatter(xy[:, 0], xy[:, 1], s=1.5, c="#E24B4A")
        top.set_title(f"{frame_time(im.name):.0f} s · {len(xy)} points", fontsize=8)
        bottom.imshow(grey, cmap="gray")
        for x1, y1, x2, y2 in seg:
            bottom.plot([x1, x2], [y1, y2], color="#1D9E75", lw=0.8)
        bottom.set_title(f"{len(seg)} line segments", fontsize=8)
        top.axis("off"); bottom.axis("off")
    fig.tight_layout(); fig.savefig(OUT / "fig2_frames.png", dpi=200); plt.close(fig)

    # Fig 3: registration and points per frame against image speed
    kept = sorted((work / "frames").glob("*.jpg"))
    t_kept = np.array([frame_time(p.name) for p in kept])
    seen = {im.name: im.num_points3D for im in rec.images.values()}
    ok = np.array([p.name in seen for p in kept]); pts = np.array([seen.get(p.name, 0) for p in kept])
    s3 = stats["clip3"]
    fig, a = plt.subplots(figsize=(7, 2.4))
    a.bar(t_kept[ok], pts[ok], width=0.2, color="#1D9E75", label="3D points seen")
    a.plot(t_kept[~ok], np.zeros((~ok).sum()), "x", color="#E24B4A", label="not registered")
    a.set_xlabel("time in clip 3 (s)"); a.set_ylabel("3D points seen")
    b = a.twinx(); b.plot(s3["t"], s3["motion"], color="#888888", lw=1, label="image speed"); b.set_ylabel("image speed (px/s)")
    b.set_ylim(0, 400); b.spines["top"].set_visible(False)
    h1, l1 = a.get_legend_handles_labels(); h2, l2 = b.get_legend_handles_labels()
    a.legend(h1 + h2, l1 + l2, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "fig3_registration.png", dpi=200); plt.close(fig)

    cloud = nb["clean"](nb["to_cloud"](rec))

    # Numbers the report quotes
    rank = lambda a: np.argsort(np.argsort(a))  # noqa: E731
    for name, s in stats.items():
        m = ~np.isnan(s["motion"])
        print(f"{name}: rank corr speed vs sharpness {np.corrcoef(rank(s['motion'][m]), rank(s['sharpness'][m]))[0, 1]:.2f}")
    summary = nb["summary"](rec, n_input=len(kept))
    print("SfM:", summary, "| focal px", round(rec.cameras[1].params[0]))
    for thr in (1.0, 1.5, 2.0):
        print(f"smooth thr {thr}: area / points %", [round(float(x), 1) for x in nb["smooth_share"](rec, work / "frames", thr=thr)])
    valid = ~np.isnan(s3["motion"])
    speed = np.interp(t_kept[ok], s3["t"][valid], s3["motion"][valid])
    print(f"not registered: {(~ok).sum()} frames, {t_kept[~ok].min():.1f}-{t_kept[~ok].max():.1f} s; "
          f"rank corr points vs speed {np.corrcoef(rank(pts[ok]), rank(speed))[0, 1]:.2f}")
    speed_all = np.interp(t_kept, s3["t"][valid], s3["motion"][valid])
    print(f"image speed px/s: registered median {np.median(speed_all[ok]):.0f}, fastest {speed_all[ok].max():.0f}; "
          f"not registered median {np.median(speed_all[~ok]):.0f}, range {speed_all[~ok].min():.0f}-{speed_all[~ok].max():.0f}")

    # Part 3: lines instead of points (same steps as the notebook's run cells)
    n_seg = [len(nb["detect_lines"](cv2.imread(str(work / "frames" / im.name), cv2.IMREAD_GRAYSCALE))) for im in ims]
    print(f"segments per registered frame: median {np.median(n_seg):.0f}; "
          f"3D points seen per frame: median {np.median([im.num_points3D for im in ims]):.0f}")
    planes = nb["segment_planes"](rec, work / "frames")
    up_cam = nb["gravity_frame"](cloud)[1]
    up = nb["vertical_direction"](planes, up_cam)
    cr, ur, keep = nb["vertical_rays"](planes, up)
    B = nb["top_view"](up); pts2d = cloud.xyz @ B.T; cell = 0.01
    lo = np.percentile(pts2d, 2, axis=0) - 0.3; hi = np.percentile(pts2d, 98, axis=0) + 0.3
    sharp = nb["sharpen"](nb["vote"](cr, ur, lo, hi, cell))
    print(f"segments {len(planes.normals)}, near-vertical {keep.sum()} ({100 * keep.mean():.0f} %); "
          f"vertical vs camera up {np.degrees(np.arccos(np.clip(up @ up_cam, -1, 1))):.1f} deg")
    xy, w = nb["find_peaks"](sharp, lo, cell)
    origin, axis, on_row = nb["fit_row"](xy, w)
    extent = np.abs((xy[on_row] - origin) @ axis).max() + 0.2
    grid_xy = lo + (np.argwhere(np.ones_like(sharp, bool))[:, ::-1] + 0.5) * cell
    votes_w = np.clip(sharp, 0, None).ravel()
    print(f"peaks on row: {on_row.sum()} of {len(xy)}")
    for hw in (0.05, 0.1, 0.2):
        pl = nb["period"](nb["profile_along"](grid_xy, votes_w, origin, axis, hw, cell, extent), cell, 0.06, 0.5)
        pp = nb["period"](nb["profile_along"](pts2d, np.ones(len(pts2d)), origin, axis, hw, cell, extent), cell, 0.06, 0.5)
        print(f"band {hw}: period lines {pl[0]:.2f} (ac {pl[1]:.2f}), points {pp[0]:.2f} (ac {pp[1]:.2f})")
    prof_l = nb["profile_along"](grid_xy, votes_w, origin, axis, 0.1, cell, extent)
    spacing_u = nb["period"](prof_l, cell, 0.06, 0.5)[0]
    h = np.concatenate([nb["end_heights"](planes, keep, cr, ur, up, x0) for x0 in xy[on_row]])
    tape = nb["GT"]["measured"]
    for q in (1, 2):
        bottom, top = np.percentile(h, [q, 100 - q])
        print(f"height {q}-{100 - q} pct: {top - bottom:.2f} units -> spacing "
              f"{tape['radiator_height'] * spacing_u / (top - bottom):.1f} mm (tape {tape['tube_center_spacing']})")

    # Fig 4: the SfM points alone, and with the vertical lines, from above and from the front
    segments = nb["vertical_segments"](planes, keep, cr, ur, up, xy[on_row])
    s_row = (xy[on_row] - origin) @ axis
    print(f"vertical lines: {len(segments)} over {np.ptp(s_row):.2f} units = {np.ptp(s_row) / spacing_u:.1f} spacings")
    Ru = nb["upright_frame"](cloud, up); mu = cloud.xyz.mean(0)
    p = (cloud.xyz - mu) @ Ru.T; c = (cloud.cam_centers - mu) @ Ru.T; e = (segments - mu) @ Ru.T
    fig, ax = plt.subplots(2, 2, figsize=(7, 4.4))
    for row, with_lines in enumerate((False, True)):
        for a, (i, j, flip, title) in zip(ax[row], [(0, 2, -1, "from above"), (0, 1, 1, "from the front")]):
            a.scatter(p[:, i], flip * p[:, j], s=0.4, c="#BBBBBB" if with_lines else cloud.rgb / 255)
            a.plot(c[:, i], flip * c[:, j], "-", color="#E24B4A", lw=1)
            if with_lines:
                for s0, s1 in e:
                    a.plot([s0[i], s1[i]], [flip * s0[j], flip * s1[j]], color="#1D9E75", lw=1.2,
                           marker="o" if j == 2 else None, ms=2)
            a.set_title(f"{title} · {'points and lines' if with_lines else '3D points only'}", fontsize=8)
            a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([])
            for side in a.spines.values(): side.set_visible(False)
    fig.tight_layout(); fig.savefig(OUT / "fig4_model.png", dpi=200); plt.close(fig)
    print("figures in", OUT)


if __name__ == "__main__":
    main()
