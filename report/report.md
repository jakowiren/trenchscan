# Trenchscan: phone video to 3D, tested on a radiator

<p class="byline">Jakob Wirén · October 2026 · Hand-in: repository, notebook <code>notebooks/01_sparse_reconstruction.ipynb</code>, this report. References such as §2.4 point to notebook sections.</p>

## 1 Goal

sizeless documents underground utilities from a phone video. A crew films an open trench with an iPhone Pro for about ten minutes; sizeless builds a metric 3D model, recognises pipes, fittings and couplings, and delivers CAD and GIS as-built plans, according to its [website](https://sizeless.co/en) and [Y Combinator page](https://www.ycombinator.com/companies/sizeless). This project aims to understand the work behind such a product. It rebuilds the first stage, from video to 3D, with standard tools on a stand-in scene, to see what a phone video gives classical reconstruction, where it breaks, and so what a product like sizeless has to solve.

## 2 Setup

The stand-in for a trench is a white column radiator in my apartment. Its vertical tubes play the pipes. The capture shares the constraints of a trench: a modest phone (Oppo A38, 720p maximum), no markers on the surfaces, limited stand-off (furniture and a corner), and smooth, uniform surfaces. The right end stands in a corner and cannot be filmed, so before any processing it is clear the model will be weak on that side.

![The radiator in clips 1, 2 and 3](figures/fig1_scene.jpg)
<p class="caption">Figure 1. One frame per clip: top-down with a bank card, side view of the left end, front view.</p>

| Clip | Length | How it was filmed | Stored as |
|---|---|---|---|
| 1 | 47 s | Top-down along the radiator, two bank cards on the floor | landscape |
| 2 | 46 s | Side view of the left end, then close to the tubes | portrait |
| 3 | 36 s | Arc from the left end round to the front, ending close | portrait |

Tape-measured ground truth: tube circumference 90 mm (diameter 28.6 mm), tube spacing 55 mm centre to centre, radiator height 960 mm. Two bank cards (85.6 × 54.0 mm) on the floor were filmed as a scale reference; they are not used yet (Section 7).

The pipeline for clip 3: frames at 4 fps, a blur filter that keeps the sharpest 75 %, then SfM with COLMAP through pycolmap (SIFT features, sequential matching, incremental mapping) on a CPU, in about a minute.

## 3 Theory in brief

The task is to turn a video into a 3D model that can be measured. Follow one capture through the steps.

- **Filming creates parallax.** A worker at sizeless walks along the trench and films it. Every frame shows the same pipes from a slightly different position. *Parallax* is the apparent shift of an object between two views taken from different places: near things shift more than far things, as a finger held up does when you close one eye and then the other. That shift is what reveals depth. It needs a *baseline*, a distance between the two camera positions; a camera that only turns on the spot gives none.
- **Features link the frames.** To use parallax, the software must find the same physical spot in different frames. It looks for *features*: small, distinctive patches such as a corner, a speck or a printed letter. The classic detector, [SIFT](https://www.cs.ubc.ca/~lowe/papers/ijcv04.pdf), finds small spots that stand out from their surroundings and describes each by the pattern of brightness changes around it, so it can be recognised in the next frame. A smooth surface with soft shading has no such spots. On a clean white pipe there is nothing to hold on to.
- **Geometry finds the cameras and the points.** Some matches are wrong. All correct matches between two frames must agree with one single camera movement (*epipolar geometry*), so a voting method, RANSAC, keeps the matches that agree and drops the rest. *Structure-from-motion* (SfM, here [COLMAP](https://openaccess.thecvf.com/content_cvpr_2016/papers/Schonberger_Structure-From-Motion_Revisited_CVPR_2016_paper.pdf)) then works out where the camera stood for each frame and where each matched spot sits in 3D, by intersecting the viewing rays from two or more camera positions (*triangulation*). It adds frames one at a time, placing each new camera from 3D points it already sees. Last, *bundle adjustment* fine-tunes all cameras and points together so that every 3D point, projected back into a frame, lands where it was seen. The distance left over, in pixels, is the *reprojection error*; well under a pixel means the model is consistent. sizeless runs the same ideas live, while filming, as SLAM (simultaneous localisation and mapping).
- **Scale is missing.** Images alone cannot tell a small pipe filmed close up from a large pipe filmed from further away: scaling the scene and the camera path together gives exactly the same frames ([Hartley and Zisserman](https://www.robots.ox.ac.uk/~vgg/hzbook/)). The model has the right shape but no units, until something of known length is in view, such as a card, or a sensor measures the phone's movement in metres.
- **Measuring the video.** Two numbers describe each frame here. *Sharpness* is the [variance of the Laplacian](https://doi.org/10.1109/ICPR.2000.903548), a filter that responds to fine detail; blur smears detail away, so a blurred frame scores low. *Image speed* is how fast the picture moves across the screen, in pixels per second, taken as the median *optical flow* ([Farnebäck](https://doi.org/10.1007/3-540-45103-X_50)), the estimated movement of each pixel between two frames.

## 4 Findings

### 4.1 The data (§1.1–1.4)

- **One camera, three ways of filming.** All clips are H.264, 1280 × 720 at 8.4 Mbit/s. Clip 1, filmed towards the floor, is stored landscape; clips 2 and 3 are portrait. The frame rate is variable (27.7–29.1 fps on average) and clip 2 drops the most frames (71 gaps).
- **Coverage is one-sided.** The left side and the front are covered. The right end stands in a corner and was never filmed. The bank cards appear in clip 1 and early in clip 2, not in clip 3. Feet are in most of clip 1.
- **Sharpness does not follow speed.** The rank correlation between image speed and sharpness is weak in every clip (−0.21, 0.26, −0.05). Clip 2's softest stretch is nearly still and shows bare wall (Figure 2). The Laplacian score mixes up *blurry* with *featureless*.
- **Few features, none on the tubes.** Even the sharpest frame of each clip has only 235–1,298 SIFT keypoints. They lie on tube edges, gaps, floor grain and the cards. The tube faces are almost empty.

![Sharpness and image speed over time](figures/fig2_quality.png)
<p class="caption">Figure 2. Sharpness (log scale) and image speed per clip; thin lines raw, thick lines a 1 s rolling median.</p>

### 4.2 The reconstruction of clip 3 (§2.1–2.4)

| Frames extracted | Kept by blur filter | Registered | 3D points | Reprojection error | Views per point | Focal length |
|---|---|---|---|---|---|---|
| 143 | 107 | 87 (81 %) | 3,594 | 0.66 px | 6.5 | 1093 px (36° × 61°) |

- **The blur filter removes content, not only blur.** 10 of its 36 rejected frames come from the first 5 s, where the camera moves at about 8 px/s and much of the view is plain wall (§2.1).
- **Smooth surfaces are invisible to the model.** Regions without fine detail, the shaded tube faces and the wall, cover 57 % of an average frame but hold 4 % of the 3D points (Figure 3). The threshold changes the numbers, not the picture: 43–67 % of the area holds 2–7 % of the points (§2.4).
- **The model breaks in the fastest, closest stretch.** All 20 unregistered frames lie between 28 and 35.5 s, the fast close-up at the end; once the chain of frames breaks there, it does not recover. 3D points seen per frame drop from about 390 to about 90 as image speed rises from about 30 to 150 px/s (rank correlation −0.62, Figure 4). Speed alone does not separate the frames, though: every failed frame is slower than the fastest registered one, and speed rises together with closeness, so one clip cannot tell the two apart.
- **The geometry is right where there is texture.** The camera path is a smooth arc at a nearly constant distance. The points outline vertical edges and the top and bottom of the radiator; between them, where the tube faces are, the model is almost empty (Figure 5). The model has no units: the camera path is 15.5 model units long.

![Smooth regions and 3D points](figures/fig3_points.png)
<p class="caption">Figure 3. Blue: regions without fine detail. Red: keypoints that became 3D points.</p>

![Registration against image speed](figures/fig4_registration.png)
<p class="caption">Figure 4. 3D points seen per kept frame of clip 3, frames that failed to register, and image speed (capped at 400 px/s).</p>

![Point cloud and camera path](figures/fig5_cloud.png)
<p class="caption">Figure 5. Sparse point cloud with the camera path (red), from above and from the front.</p>

## 5 Trial: lines instead of points (§3.1–3.3)

**Why.** The reconstruction left the tubes out, and Figure 3 shows why. The tube faces are smooth, and the gaps between the tubes are long straight edges. A feature has to stand out in every direction, but a spot on a straight edge looks like the next spot along it (the *aperture problem*), so SIFT finds points only where an edge ends or turns. A line as a whole, though, is easy to find. The question for the trial: are the tubes in the frames as lines?

**Why this method.** It reuses what worked and adds one assumption.

- The camera poses from SfM, the reliable part of §4.2, are reused as they are.
- [LSD](https://www.ipol.im/pub/art/2012/gjmr-lsd/), a line-segment detector that ships with OpenCV, finds the segments.
- The tubes are vertical. Seen from above, a vertical line is a single point. A segment in one frame and that frame's camera centre span a plane, and seen from above that plane is a ray from the camera through the line. The rays of one tube from many frames cross at one spot, so counting rays per grid cell (a Hough-style vote) finds the tubes without matching lines between frames.

General line mappers ([Line3D++](https://github.com/manhofer/Line3Dpp), [LIMAP](https://arxiv.org/abs/2303.17504)) handle lines in any direction but need a C++ build. The vertical shortcut is a few notebook cells, enough to answer the question.

**Result.**

- LSD finds a median of 160 segments of 40 px or more per frame, along the tube edges and gaps (Figure 6), including frames where few 3D points survived.
- 90 % of the 13,099 segments are near-vertical. The vertical estimated from them is 10.8° off the camera-based guess, which assumed the phone was held upright.
- From above, the votes form a row of compact, evenly spaced spots along the radiator front: 18 of the 27 strongest spots lie on one line. The 3D points lie in the same area but scatter over it (Figure 6).
- Along that row the votes repeat every 0.36–0.37 model units (autocorrelation 0.42–0.67, depending on the width of the band around the row). The 3D points repeat only weakly (0.30–0.33), and in the widest band they lock onto half the distance (Figure 7).
- The segment ends stop sharply at the top and bottom of the tubes, 6.0–6.2 units apart. Spacing over height is a ratio, so it needs no scale: it gives 56–58 mm for the 960 mm radiator, against 55 mm on the tape.

![Line segments and votes from above](figures/fig6_lines.png)
<p class="caption">Figure 6. Left: LSD segments on the 15 s frame. Right: the radiator front seen from above; dark spots are vertical lines found by the vote, red dots are the 3D points from SfM.</p>

![Repeat along the radiator front and segment heights](figures/fig7_spacing.png)
<p class="caption">Figure 7. Left: line votes and 3D points along the radiator front, each scaled to its maximum. Right: heights of the segment ends on the row; dashed lines at the 2nd and 98th percentiles.</p>

**The two approaches in one model.** Figure 8 shows the SfM points alone and with the vertical lines, each line running from where its segments start to where they end. From the front, the points outline the radiator: its left edge and bands along the top and bottom. The 18 lines stand between those bands, across the radiator front the points left empty, and their ends meet the bands. There are more lines than tubes, though: 18 lines over 7.3 tube spacings, because one tube gives more than one line, its edges and the gaps beside it.

![SfM points alone and with the vertical lines](figures/fig8_points_and_lines.png)
<p class="caption">Figure 8. Top: the SfM model of §4.2 (as in Figure 5). Bottom: the same points (grey) with the vertical lines from the vote (green). Camera path in red. Both use the vertical estimated from the lines.</p>

**What it shows.** The tube structure is in the video, as lines, and points miss most of it. The final model gains the radiator front, as lines rather than surfaces. The trial gives positions, not diameters: a tube's visible edge is where the line of sight grazes the cylinder, which moves with the camera, so a diameter needs a cylinder fitted to those edges. It relies on vertical tubes, while trench pipes mostly run horizontally along the trench, so the vote would have to run along the pipe direction, or a general line mapper takes over. And it assumes the segments span the full height of the radiator, which the sharp top and bottom in Figure 7 support.

## 6 Discussion: what this means for a product like sizeless

1. **Poses are easy, the objects are hard.** The camera path is reasonable, but the pipes themselves, smooth and uniform, carry almost no points and therefore feature extraction is hard. In a trench, PVC, painted steel and water behave the same way. sizeless reports pipe diameters as an output ([YC page](https://www.ycombinator.com/companies/sizeless)); our evidence says surface points from classical features would not support that. Shape has to come from edges and silhouettes, or from methods that do not depend on texture. Section 5 tries the edges.
2. **Guide the capture with image speed.** Speed probably correlates with the loss of points (rank correlation −0.62, §2.4); the sharpness score does not, and it discards sharp frames of bare surfaces. A capture app can measure optical flow live and warn before the frames are lost.
3. **Coverage is decided on site.** The unfilmed corner cannot be recovered later. Once a trench is backfilled, neither can the trench, so the app has to show what is missing while the crew is still there.
4. **Scale must be built in.** Our model has no units. sizeless captures with an iPhone Pro and builds a metric model in its SLAM engine ([website](https://sizeless.co/en), [YC page](https://www.ycombinator.com/companies/sizeless)); a card or something of known size in view is only a fallback, and only if it is in the clip that gets reconstructed, which it was not in this case.
5. **Real scenes move.** Feet already disturb clip 1. sizeless names wet, muddy trenches with moving excavators as what breaks off-the-shelf reconstruction ([YC page](https://www.ycombinator.com/companies/sizeless)).

| Step | sizeless | This demo |
|---|---|---|
| Capture | Guided iPhone Pro app, about 10 min per trench, works without GPS | Unguided 36–47 s clips from a 720p phone |
| 3D | Metric 3D model from a SLAM engine, built for wet trenches with moving machines | Sparse SfM, about 3,600 points, no scale, static scene |
| Components | Pipe types, diameters, fittings, couplings | None |
| Measurements | Measurements and billable quantities | Tube spacing relative to height, from lines (Section 5); tape ground truth recorded |
| Output | CAD (DWG/DXF), BIM/GIS, crew voice notes anchored in 3D | Interactive 3D view |

Sources for sizeless: [website](https://sizeless.co/en), [YC page](https://www.ycombinator.com/companies/sizeless), [App Store listing](https://apps.apple.com/us/app/sizeless-sitescan/id6748157116).

## 7 Future work

Each step follows from a finding and can be scored with data this project already has.

| Finding | Next step | Evaluation |
|---|---|---|
| No scale (§2.2) | Scale from the bank card; combine clip 1, rotated, with clip 3 | Tube spacing 55 mm and height 960 mm against the tape |
| Smooth tubes hold 4 % of points (§2.4) | Learned matching ([SuperPoint](https://arxiv.org/abs/1712.07629) + [LightGlue](https://arxiv.org/abs/2306.13643)) or learned reconstruction ([MASt3R](https://arxiv.org/abs/2406.09756), [VGGT](https://arxiv.org/abs/2503.11651)) | Point share in smooth regions |
| Lines find the tubes, but only vertical ones and no diameter (§3.3) | Cylinders fitted to the tube edges; line mapping in any direction ([LIMAP](https://arxiv.org/abs/2303.17504)), tried on horizontal pipes | Diameter 28.6 mm; spacing 55 mm |
| Points fall as speed rises (§2.4) | Live speed warning from optical flow during capture | Share of frames that register |
| Blur score drops sharp, bare frames (§2.1) | Select frames by speed and overlap instead of Laplacian variance | Registered frames and points per frame |
| Moving objects in view (§1.2) | Mask people before matching | Reprojection error and outliers with and without masks |

## 8 Limitations

Just capture more data, and learn by trial and error what types of data make reconstruction better. The smooth-region measure covers wall and tube faces together, because nothing segments the radiator yet. Its threshold was chosen by eye, so results are reported over a range. The texture check in §1.4 uses OpenCV's SIFT, not COLMAP's.
