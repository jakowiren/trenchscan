"""Build report/report.pdf from report/report.md with headless Chrome.

    python report/make_figures.py   # once, after running the notebook
    python report/build.py

Needs the `markdown` package (requirements.txt) and Google Chrome or Chromium on the PATH.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
CSS = """
@page { size: A4; margin: 16mm 17mm 16mm 17mm; }
body { font-family: "Helvetica Neue", Arial, sans-serif; font-size: 9.6pt; line-height: 1.42; color: #1a1a1a; }
h1 { font-size: 17pt; margin: 0 0 2mm; }
h2 { font-size: 12pt; margin: 6mm 0 1.5mm; border-bottom: 0.4pt solid #bbb; padding-bottom: 0.8mm; }
h3 { font-size: 10.4pt; margin: 4mm 0 1mm; }
p, li { margin: 0 0 1.6mm; }
ul, ol { padding-left: 5mm; margin: 0 0 2mm; }
.byline { color: #555; font-size: 8.6pt; margin-bottom: 4mm; }
code { font-size: 8.4pt; }
img { display: block; max-width: 100%; margin: 2mm auto 0.5mm; }
figure { margin: 0 0 3mm; break-inside: avoid; }
figcaption, .caption { font-size: 8.2pt; color: #555; margin: 0; text-align: center; }
table { border-collapse: collapse; width: 100%; font-size: 8.4pt; margin: 1.5mm 0 3mm; break-inside: avoid; }
th, td { border-bottom: 0.4pt solid #ccc; padding: 1mm 1.6mm; text-align: left; vertical-align: top; }
th { background: #f2f2f2; }
img, .caption, li { break-inside: avoid; }
h2, h3 { break-after: avoid; }
a { color: #1F5FA8; text-decoration: none; }
"""


def find_chrome() -> str:
    for name in ("google-chrome", "chromium", "chromium-browser"):
        if path := shutil.which(name):
            return path
    sys.exit("Chrome or Chromium not found on PATH")


def main() -> None:
    body = markdown.markdown((HERE / "report.md").read_text(encoding="utf-8"), extensions=["tables"])
    # keep each image with its caption on one page
    body = re.sub(r'<p>(<img [^>]+>)</p>\s*<p class="caption">(.*?)</p>', r"<figure>\1<figcaption>\2</figcaption></figure>", body, flags=re.S)
    html = HERE / "report.html"
    html.write_text(f'<!doctype html><html><head><meta charset="utf-8"><title>Trenchscan report</title>'
                    f"<style>{CSS}</style></head><body>{body}</body></html>", encoding="utf-8")
    pdf = HERE / "report.pdf"
    subprocess.run([find_chrome(), "--headless", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", html.as_uri()], check=True, capture_output=True)
    print("wrote", pdf)


if __name__ == "__main__":
    main()
