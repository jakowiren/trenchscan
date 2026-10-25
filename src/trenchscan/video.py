"""Looking at the raw clips: metadata, frames at given times, contact sheets, previews (notebook Part 1)."""

from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import HTML


def make_preview(video: Path, out_dir: Path, long_side: int = 640) -> Path:
    """Small H.264 copy for viewing: displayed orientation, no audio, a few MB. Cached in out_dir."""
    out = Path(out_dir) / f"{video.stem}_{long_side}.mp4"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        scale = f"scale='if(gt(iw,ih),{long_side},-2)':'if(gt(iw,ih),-2,{long_side})'"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-an", "-vf", scale,
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(out)], check=True)
    return out


def video_grid(previews: dict[str, Path], height: int = 400, captions: dict[str, str] | None = None) -> HTML:
    """Side-by-side players. Videos are embedded (base64), so they play without a file server."""
    figs = []
    for name, path in previews.items():
        b64 = base64.b64encode(path.read_bytes()).decode()
        figs.append(f'<figure style="margin:0"><video controls muted preload="metadata" '
                    f'style="height:{height}px;max-width:100%" src="data:video/mp4;base64,{b64}"></video>'
                    f'<figcaption style="font-size:12px">{(captions or {}).get(name, name)}</figcaption></figure>')
    return HTML('<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end">' + "".join(figs) + "</div>")


def ffprobe_json(video: Path, *args: str) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-of", "json", *args, str(video)],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def frame_times(video: Path) -> np.ndarray:
    """Presentation timestamps (s) of every video frame, sorted."""
    d = ffprobe_json(video, "-select_streams", "v:0", "-show_entries", "packet=pts_time")
    return np.sort([float(p["pts_time"]) for p in d["packets"] if p.get("pts_time", "N/A") != "N/A"])


def probe(video: Path) -> dict:
    d = ffprobe_json(video, "-select_streams", "v:0", "-show_entries",
                     "stream=codec_name,width,height,bit_rate:stream_side_data=rotation:format=duration")
    s = d["streams"][0]
    rotation = next((int(sd["rotation"]) for sd in s.get("side_data_list", []) if "rotation" in sd), 0)
    w, h = s["width"], s["height"]
    t = frame_times(video)
    dt = np.diff(t) * 1000
    return {
        "codec": s["codec_name"],
        "stored": f"{w}x{h}",
        "rotation": rotation,
        "displayed": f"{h}x{w}" if rotation % 180 else f"{w}x{h}",
        "duration_s": round(float(d["format"]["duration"]), 1),
        "frames": len(t),
        "mean_fps": round((len(t) - 1) / (t[-1] - t[0]), 2),
        "frame_dt_ms min/med/max": f"{dt.min():.0f}/{np.median(dt):.0f}/{dt.max():.0f}",
        "gaps > 1.5x median": int((dt > 1.5 * np.median(dt)).sum()),
        "bitrate_mbps": round(int(s.get("bit_rate", 0)) / 1e6, 1),
    }


def print_table(rows: dict[str, dict]) -> None:
    keys, names = list(next(iter(rows.values()))), list(rows)
    w = max(len(k) for k in keys)
    print(" " * w + "".join(f"{n:>14}" for n in names))
    for k in keys:
        print(f"{k:<{w}}" + "".join(f"{str(rows[n][k]):>14}" for n in names))


def read_at(video: Path, times_s) -> list[np.ndarray]:
    """RGB frames at the given times. OpenCV applies the rotation metadata, so frames come out as displayed."""
    cap = cv2.VideoCapture(str(video))
    frames = []
    for t in times_s:
        cap.set(cv2.CAP_PROP_POS_MSEC, 1000 * t)
        ok, bgr = cap.read()
        if ok:
            frames.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    cap.release()
    return frames


def contact_sheet(video: Path, duration_s: float, n: int = 12, cols: int = 6, title: str = "") -> plt.Figure:
    times = (np.arange(n) + 0.5) * duration_s / n
    frames = read_at(video, times)
    rows = int(np.ceil(n / cols))
    h, w = frames[0].shape[:2]
    fig, ax = plt.subplots(rows, cols, figsize=(2.6 * cols, rows * 2.6 * h / w + 0.6), squeeze=False)
    for a in ax.flat:
        a.axis("off")
    for a, t, f in zip(ax.flat, times, frames):
        a.imshow(f)
        a.set_title(f"{t:.1f} s", fontsize=9)
    fig.suptitle(title)
    fig.tight_layout()
    return fig
