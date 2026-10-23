# Capture log & findings

## Capture 1 — 2026-10-23, column radiator, apartment

**Setup**
- Target: white cast-iron column radiator (vertical tubes ≈ cylinders), bank card on floor for scale (85.6 × 54 mm)
- Phone: max video resolution 1280×720 (no 4K available)
- 3 clips: 47 s (top-down, card visible), 46 s (arc, then close-up), 36 s (arc)
- Constraints: no surface prep (no tape/markers), furniture limits stand-off distance

**Ground truth (tape, mm)** — see `data/ground_truth/radiator_2026-10-23.yaml`
| Quantity | Value |
|---|---|
| Tube circumference | 90 (→ diameter 28.6) |
| Tube centre-to-centre spacing | 55 |
| Radiator height (top to bottom) | 960 |
| Radiator bottom to floor | 160 |

**Result — clip 3, CPU only (pycolmap 4.0, SIFT, sequential matching)**
| Metric | Value |
|---|---|
| Frames extracted (4 fps) | 143 |
| Kept after blur filter (top 75% Laplacian variance) | 107 |
| Registered | 87 (81%) |
| Sparse points (filtered) | ~3,070 |
| Mean reprojection error | 0.67 px |
| Runtime (2 CPU cores) | ~1 min |

**Observations**
1. Camera poses are solid; scene structure (wall corner, skirting board, radiator outline) is recognisable.
2. Radiator surfaces are nearly empty: smooth white paint gives SIFT almost nothing. Only edges and shadowed gaps produce points.
3. Second half of clip 2 is unusable: too close + fast motion → blur.
4. Card is clearly visible in clip 1 and the start of clips 2–3 → scale recovery feasible.

## Why these constraints matter (link to production)
The constraints here mirror real trench capture rather than being lab artefacts:
- **Fixed, modest phone hardware** — crews use what they have; pipeline can't assume 4K.
- **No surface preparation** — nobody tapes pipes in a trench.
- **Limited stand-off** — a trench physically prevents stepping back, like furniture here.
- **Low-texture, uniform surfaces** — white radiator ≈ smooth/wet PVC or painted steel pipes.

**Implications / ideas to test**
- Textureless surfaces → classical SIFT+MVS will under-reconstruct the very objects we care about. Candidates: learned matchers (SuperPoint+LightGlue), learned reconstruction (VGGT / MASt3R), or fitting primitives (cylinders) from edges/silhouettes rather than surface points.
- Close range + blur → capture-time guidance in the app (live blur/speed warning) is cheaper than fixing it in post.
- Scale → phone IMU/ARKit-ARCore metric scale in production; card/marker as a fallback and as ground truth for evaluation.

## Open
- [x] Tape-measure ground truth (circumference, spacing, height, floor clearance)
- [ ] Combine clips 1 + 3 (adds top-down view + card)
- [ ] Try a learned matcher / VGGT on the same frames and compare point density on the tubes
