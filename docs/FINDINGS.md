# Capture log & findings

## Capture 1 — 2026-10-23, column radiator, apartment

**Setup**
- Target: white cast-iron column radiator (vertical tubes ≈ cylinders), two bank cards on the floor for scale (85.6 × 54 mm)
- Phone: Oppo A38, max video resolution 1280×720 (no 4K available)
- 3 clips: 47 s (top-down, cards visible), 46 s (side view of the left end, then close-up), 36 s (arc from the left end to the front)
- Constraints: no surface prep (no tape/markers), furniture limits stand-off distance

**Ground truth (tape, mm)** — see `data/ground_truth/radiator_2026-10-23.yaml`
| Quantity | Value |
|---|---|
| Tube circumference | 90 (→ diameter 28.6) |
| Tube centre-to-centre spacing | 55 |
| Radiator height (top to bottom) | 960 |
| Radiator bottom to floor | 160 |

**Result — clip 3, CPU only (pycolmap 4.2.1, SIFT, sequential matching; the run the report quotes)**
| Metric | Value |
|---|---|
| Frames extracted (4 fps) | 143 |
| Kept after blur filter (top 75% Laplacian variance) | 107 |
| Registered | 87 (81%) |
| Sparse points | 3,594 |
| Mean reprojection error | 0.66 px |
| Runtime (CPU) | ~1 min |

**Observations**
1. Camera poses are solid; scene structure (wall corner, skirting board, radiator outline) is recognisable.
2. Radiator surfaces are nearly empty: smooth white paint gives SIFT almost nothing. Only edges and shadowed gaps produce points.
3. Second half of clip 2 is close and fast, but much of its low sharpness is bare surface rather than blur (notebook 1.3).
4. The cards are visible in clip 1 and early in clip 2, not in clip 3 (notebook 1.2) → scale needs clip 1 or 2 combined with clip 3. Not used yet.

## Parameter variations — 2026-10-25, clip 3
One setting changed at a time in the notebook's run cells (2.1 frames, 2.2 SfM), everything else at baseline (4 fps, keep 0.75, overlap 12). Each run twice, since SfM is not deterministic; ranges are the two runs.

| Variant | Frames into SfM | Registered | Models | 3D points | Views per point | Model covers |
|---|---|---|---|---|---|---|
| Baseline | 107 of 143 | 87 (81 %) | 1 | 3,603–3,612 | 6.5 | 0–27 s |
| keep 0.5 (stricter blur filter) | 72 of 143 | 32 (44 %) | 2–3 | 1,733–1,738 | 5.7 | 0–16.5 s |
| keep 0.9 (looser blur filter) | 128 of 143 | 106 (83 %) | 1 | 3,910–3,930 | 6.9 | 0–28.5 s |
| fps 2 | 54 of 72 | 27–29 (50–54 %) | 2 | 1,221–1,236 | 5.3 | 0–18/19 s |
| fps 6 | 161 of 215 | 133 (83 %) | 1 | 4,868–4,910 | 8.1 | 0–28.5 s |
| overlap 5 | 107 of 143 | 87 (81 %) | 1 | 3,616–3,627 | 6.4–6.5 | 0–27 s |
| overlap 25 | 107 of 143 | 87 (81 %) | 1 | 3,600–3,631 | 6.5 | 0–27 s |

Reprojection error stays 0.50–0.70 px in every run. SfM takes 13–48 s on this machine; overlap 5 vs 25 is within run-to-run noise.

1. **A stricter blur filter is worse.** keep 0.5 removes frames, the gaps between neighbours grow, and the model breaks at about 17 s into separate pieces. keep 0.9 registers more frames and points than the baseline. What SfM needs is overlap between consecutive frames, more than sharpness of each frame (fits 2.1: the filter drops bare frames, not just blurry ones).
2. **Denser sampling helps, sparser breaks.** fps 2 breaks at 18–19 s, like keep 0.5. fps 6 gives the most points and the longest tracks (8.1 views per point).
3. **Overlap 5 to 25 changes nothing here.** The camera moves smoothly along one arc, so a frame only matches its near neighbours anyway; more candidate pairs add no new matches. A capture that revisits a place (a loop) would need wider overlap or loop detection.
4. **No setting recovers the end of the clip.** Every variant loses the fast close-up after 28.5 s (2.4). That failure is in the capture, not the settings.

## Line trial — 2026-10-25, clip 3 (notebook Part 3, report Section 5)
LSD line segments in the 87 registered frames, back-projected with the SfM poses, voted from above assuming vertical tubes.
1. Segments follow the tube edges and gaps where SIFT found almost no points (median 160 segments vs 279 3D points per frame).
2. From above, the votes form an evenly spaced row of spots along the radiator front, repeating every 0.36–0.37 model units; the 3D points repeat only weakly.
3. Spacing over tube height (6.0–6.2 units) gives 56–58 mm for the 960 mm radiator; tape says 55 mm. No scale reference needed for the ratio.
4. Not yet: diameters (tube edges are tangents that move with the viewpoint), and pipes that are not vertical.

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
- [ ] Fit cylinders to the tube edges from the line trial → diameter vs 28.6 mm
