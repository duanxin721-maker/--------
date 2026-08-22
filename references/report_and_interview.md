# Assignment Report Key Points & Interview Q&A

Reference for preparing the written report and oral defense. Load this when writing
the report document or rehearsing interview answers.

---

## 1. Approach Rationale

Do NOT train a deep-learning image classifier. The target is a **fixed game** whose
UI style and layout remain constant, so UI elements can serve as reliable detection
features. The pipeline is:

1. Predefine scene categories (story / battle) and the UI features that trigger each.
2. Detect UI elements in sampled frames via OpenCV template matching.
3. Classify each frame by preset rule priority (battle > story).
4. Apply temporal smoothing to eliminate single-frame jitter.
5. Output timestamped scene segments.

**Core idea:** first define feature rules, then detect features, then classify by
rules — fully explainable, no model training required.

## 2. Feature & Rule Design

### Story features
- `dialog.png` — dialogue popup window (cutscene / conversation)
- Character CG overlay with no combat controls (no HP bars, no skill bar)

### Battle features
- `player_hp.png` — player health bar
- `enemy_hp.png` — enemy health bar
- `skill_bar.png` — skill / action bar
- Combat effect UI panels

### Rule priority (critical)
1. Any battle UI detected -> `battle` (battle priority > story, even if a dialogue
   box is also present — combat can contain in-fight dialogue).
2. No battle feature but dialog detected -> `story`.
3. Nothing detected -> `unknown` (do not force-classify).

### Edge cases
- Simultaneous dialog + battle UI -> battle wins.
- A frame with zero feature matches -> `unknown`, not forced into a category.
- Temporal smoothing: N consecutive same-class frames (default N=3) required to
  confirm a scene switch; isolated anomalies inherit the last valid scene.

## 3. Technical Implementation

### UI detection
OpenCV `cv2.matchTemplate` with `TM_CCOEFF_NORMED` (normalized correlation
coefficient). A template is "hit" when max correlation >= threshold (default 0.7).
Frames are converted to grayscale before matching for robustness and speed.

### Frame sampling
Process every N-th frame (default 30, i.e. ~1 frame/sec at 30 fps). Reduces compute
without losing scene-switch signal. Each sampled frame carries a video timestamp
(`frame_index / fps`).

### Temporal smoothing
Sliding window (default size 3). A scene change is confirmed only when all frames
in the window agree. Consecutive same-class frames are merged into segments with
start/end timestamps for the final report.

## 4. Limitations & Optimization Directions (bonus)

### Limitations
- Template matching is sensitive to UI scaling and position drift; if the game UI
  changes layout or resolution, templates must be re-cropped.
- Strict threshold can miss partial / occluded UI; loose threshold can false-positive.

### Optimization directions
1. Expand the UI template library (more features -> more robust classification).
2. Replace template matching with a YOLO object detector trained on UI components for
   better robustness to scaling, partial occlusion, and layout variation.
3. Add OCR to read dialogue-box text as a secondary signal for story-scene validation.
4. Multi-scale template matching (`matchTemplate` at several scales) to handle
   resolution differences.

## 5. High-Frequency Interview Q&A

**Q: Why template matching + rules instead of training an AI image classifier?**

Because the target is a **fixed game** with constant UI appearance. The rule-based
approach is fully explainable — every classification can be traced to which UI
template was matched. It needs no large labeled dataset and no model training.
Iteration only requires updating templates or rules, no retraining. Inference is
fast. The trade-off: if the game UI changes, templates need updating.

**Q: What if a frame simultaneously detects a dialogue box and a health bar?**

By business rule, battle priority is higher than story, so the frame is classified
as `battle`. This handles the case of in-combat dialogue correctly.

**Q: Why temporal smoothing?**

A single video frame can be momentarily misclassified due to visual effects,
occlusion, or motion blur. Requiring N consecutive frames to agree before switching
scenes removes jitter and produces coherent, stable scene segments.

**Q: How is the similarity threshold chosen?**

0.7 is a balanced starting point for `TM_CCOEFF_NORMED` (range -1 to 1, higher is
more similar). Too high -> misses partial matches; too low -> false positives. In
practice, tune on a short clip of the target game and inspect hit scores.

**Q: What happens if the game UI changes resolution or layout?**

Fixed-game assumption breaks. Mitigations: crop templates at the same resolution as
the video; for variable cases, add multi-scale matching or switch to a trained YOLO
UI detector.
