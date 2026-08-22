#!/usr/bin/env python3
"""
Game Video Scene Recognize - UI template matching + rule-based classification.

For fixed-game videos where UI style/layout is constant. Detects predefined UI
templates in sampled frames via OpenCV matchTemplate, classifies each frame as
menu / battle / story / exploration / unknown by preset rule priority, then
applies temporal smoothing to remove single-frame jitter.

Supported scenes:
    menu        -> map/menu UI detected (highest priority)
    battle      -> player_hp / enemy_hp / skill_bar detected
    story       -> skip button / story UI / dialog detected (no battle UI)
    exploration -> minimap detected (no battle/story/menu UI)
    unknown     -> no matched UI features

Key design choices for transparent dialog boxes (e.g. Wuthering Waves):
    - Dialog boxes may have transparent/semi-transparent backgrounds
    - Use fixed UI chrome (skip button, story-mode top buttons) as stable story markers
    - Missing templates are skipped with a warning (not a fatal error)
    - Templates can specify a Region of Interest (ROI) for faster, more accurate matching

Usage:
    python scene_recognize.py                          # use default config
    python scene_recognize.py --video input.mp4        # override video path
    python scene_recognize.py --video x.mp4 --threshold 0.7 --interval 15

Requirements:
    pip install opencv-python
"""

import os
# Enable NVIDIA hardware decoding if available
os.environ.setdefault('OPENCV_FFMPEG_CAPTURE_OPTIONS', 'hwaccel;cuvid')

import cv2
import csv
import json
import argparse
import warnings

# ====================== Config (defaults, override via CLI) ======================
DEFAULT_VIDEO_PATH = "input.mp4"
DEFAULT_TEMPLATE_DIR = "./templates"
DEFAULT_OUTPUT_CSV = "output_scene_result.csv"
DEFAULT_MATCH_THRESHOLD = 0.7       # template match similarity threshold
DEFAULT_FRAME_SAMPLE_INTERVAL = 30   # sample 1 frame per N frames (~1/sec @30fps)
DEFAULT_SMOOTH_WINDOW = 3            # consecutive identical frames to confirm switch

# Scene priority: higher number = higher priority
SCENE_PRIORITY = {
    "menu": 4,
    "battle": 3,
    "story": 2,
    "exploration": 1,
    "unknown": 0,
}

# UI template config:
#   file   - template image filename
#   tag    - unique identifier for this UI element
#   scene  - which scene this element indicates
#   roi    - optional (x, y, w, h) region of interest as fractions of frame size
#            e.g. (0.0, 0.0, 0.15, 0.15) = top-left 15% of the frame
#            None = search the entire frame
#   required_hits - how many templates from this scene must match to confirm
#                   (default 1; increase for scenes with multiple co-occurring elements)
UI_CONFIG = [
    # ── battle features ──────────────────────────────────────────
    {"file": "player_hp.png",   "tag": "player_hp",   "scene": "battle",
     "roi": None},                            # full frame search
    {"file": "enemy_hp.png",    "tag": "enemy_hp",    "scene": "battle",
     "roi": None},                            # full frame search
    {"file": "skill_bar.png",   "tag": "skill_bar",   "scene": "battle",
     "roi": None},                            # full frame search

    # ── story features ───────────────────────────────────────────
    {"file": "skip_button.png", "tag": "skip_button", "scene": "story",
     "roi": None},                            # full frame search
    {"file": "story_ui_top.png","tag": "story_ui_top","scene": "story",
     "roi": None},                            # full frame search
    {"file": "dialog.png",      "tag": "dialog",      "scene": "story",
     "roi": None},                            # full frame search
]


def load_templates(template_dir, ui_config):
    """Load UI templates that exist on disk. Skip missing ones with a warning.

    Returns list of {"img": gray_image, "roi": roi_tuple or None, **cfg}.
    """
    templates = []
    skipped = []
    for cfg in ui_config:
        fp = os.path.join(template_dir, cfg["file"])
        if not os.path.isfile(fp):
            skipped.append(cfg["file"])
            continue
        tpl = cv2.imread(fp, cv2.IMREAD_GRAYSCALE)
        if tpl is None:
            warnings.warn(f"Template exists but cannot be read: {fp}")
            skipped.append(cfg["file"])
            continue
        templates.append({"img": tpl, "roi": cfg.get("roi"), **cfg})
    if skipped:
        print(f"[warn] Skipped {len(skipped)} missing templates: {', '.join(skipped)}")
    if not templates:
        raise FileNotFoundError(
            f"No valid templates found in {template_dir}/\n"
            f"Please prepare at least one UI template PNG before running."
        )
    return templates


def _get_roi(frame_gray, roi, frame_h, frame_w):
    """Extract a region of interest from the frame. Returns (roi_gray, (offset_x, offset_y))."""
    if roi is None:
        return frame_gray, (0, 0)
    fx, fy, fw, fh = roi
    x1 = int(fx * frame_w)
    y1 = int(fy * frame_h)
    x2 = int((fx + fw) * frame_w)
    y2 = int((fy + fh) * frame_h)
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(frame_w, x2), min(frame_h, y2)
    return frame_gray[y1:y2, x1:x2], (x1, y1)


def detect_ui_one_frame(frame_gray, templates, threshold):
    """Detect which UI templates are present in a single frame.

    Uses cv2.matchTemplate with TM_CCOEFF_NORMED within optional ROIs.
    A template is "hit" when max correlation >= threshold.
    Returns a list of hit tags, e.g. ["player_hp", "skill_bar"].
    """
    frame_h, frame_w = frame_gray.shape[:2]
    hit_tags = []
    for tpl_info in templates:
        tpl = tpl_info["img"]
        h_t, w_t = tpl.shape[:2]
        # Extract ROI for this template
        search_area, (ox, oy) = _get_roi(frame_gray, tpl_info["roi"], frame_h, frame_w)
        sa_h, sa_w = search_area.shape[:2]
        # matchTemplate requires template <= search area in both dims
        if sa_h < h_t or sa_w < w_t:
            continue
        res = cv2.matchTemplate(search_area, tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        if max_val >= threshold:
            hit_tags.append(tpl_info["tag"])
    return hit_tags


def classify_by_tags(hit_tags, templates):
    """Apply priority-based business rules to determine scene type.

    For each scene, count how many of its templates were hit.
    A scene is "active" if at least one of its templates was hit.
    The active scene with the highest priority wins.

    Priority: menu > battle > story > exploration > unknown
    """
    # Count hits per scene
    scene_hits = {}
    for tpl_info in templates:
        tag = tpl_info["tag"]
        scene = tpl_info["scene"]
        if tag in hit_tags:
            scene_hits[scene] = scene_hits.get(scene, 0) + 1

    # Pick highest-priority active scene
    best_scene = "unknown"
    best_priority = -1
    for scene, count in scene_hits.items():
        if count > 0 and SCENE_PRIORITY.get(scene, 0) > best_priority:
            best_scene = scene
            best_priority = SCENE_PRIORITY[scene]
    return best_scene


def smooth_records(raw_records, window):
    """Apply temporal smoothing: only confirm a scene change when N consecutive
    sampled frames agree on the same category. Isolated anomalies inherit the
    last valid scene.
    """
    smooth_records = []
    history = []
    last_valid_scene = "unknown"
    for rec in raw_records:
        history.append(rec["scene"])
        if len(history) > window:
            history.pop(0)
        if len(set(history)) == 1:
            last_valid_scene = history[0]
        rec["smooth_scene"] = last_valid_scene
        smooth_records.append(rec)
    return smooth_records


def build_segments(smooth_records):
    """Merge consecutive frames with the same smooth_scene into segments.
    Returns list of {scene, start_time, end_time, start_frame, end_frame}.
    """
    segments = []
    if not smooth_records:
        return segments
    cur = {
        "scene": smooth_records[0]["smooth_scene"],
        "start_frame": smooth_records[0]["frame"],
        "start_time": smooth_records[0]["time_sec"],
        "end_frame": smooth_records[0]["frame"],
        "end_time": smooth_records[0]["time_sec"],
    }
    for rec in smooth_records[1:]:
        if rec["smooth_scene"] == cur["scene"]:
            cur["end_frame"] = rec["frame"]
            cur["end_time"] = rec["time_sec"]
        else:
            segments.append(cur)
            cur = {
                "scene": rec["smooth_scene"],
                "start_frame": rec["frame"],
                "start_time": rec["time_sec"],
                "end_frame": rec["frame"],
                "end_time": rec["time_sec"],
            }
    segments.append(cur)
    return segments


def format_time(seconds):
    """Format seconds as HH:MM:SS for readability."""
    h = int(seconds) // 3600
    m = (int(seconds) % 3600) // 60
    s = int(seconds) % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def parse_time_arg(val):
    """Parse time argument in seconds or MM:SS or HH:MM:SS format."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val = str(val).strip()
    if ":" in val:
        parts = val.split(":")
        parts = [float(p) for p in parts]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return float(val)


def main():
    parser = argparse.ArgumentParser(
        description="Game video scene recognition via UI template matching + rules."
    )
    parser.add_argument("--video", default=DEFAULT_VIDEO_PATH, help="Input video path")
    parser.add_argument("--templates", default=DEFAULT_TEMPLATE_DIR, help="Template dir")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_CSV, help="Output CSV path")
    parser.add_argument("--threshold", type=float, default=DEFAULT_MATCH_THRESHOLD,
                        help="Match similarity threshold (default 0.7)")
    parser.add_argument("--interval", type=int, default=DEFAULT_FRAME_SAMPLE_INTERVAL,
                        help="Sample 1 frame per N frames (default 30)")
    parser.add_argument("--smooth", type=int, default=DEFAULT_SMOOTH_WINDOW,
                        help="Smoothing window size (default 3)")
    parser.add_argument("--start", type=str, default=None,
                        help="Start time (seconds or MM:SS or HH:MM:SS). Default: 0")
    parser.add_argument("--end", type=str, default=None,
                        help="End time (seconds or MM:SS or HH:MM:SS). Default: end of video")
    args = parser.parse_args()

    # Parse time range
    start_sec = parse_time_arg(args.start) if args.start else 0.0
    end_sec = parse_time_arg(args.end) if args.end else None

    # Load templates (skip missing ones with warning)
    templates = load_templates(args.templates, UI_CONFIG)
    # Show which templates are active
    scenes_loaded = {}
    for t in templates:
        scenes_loaded.setdefault(t["scene"], []).append(t["tag"])
    print(f"[info] Loaded {len(templates)} UI templates from {args.templates}")
    for scene, tags in scenes_loaded.items():
        print(f"       {scene}: {', '.join(tags)}")

    # Open video with ffmpeg backend for hardware acceleration
    cap = cv2.VideoCapture(args.video, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {args.video}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0
        print("[warn] Could not read FPS; assuming 30 fps")
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    print(f"[info] Video: {total_frames} frames, {fps:.1f} fps, ~{duration:.1f}s")
    if start_sec > 0:
        start_frame = int(start_sec * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        print(f"[info] Seeking to {format_time(start_sec)} (frame {start_frame})")
    else:
        start_frame = 0
    if end_sec is not None:
        print(f"[info] Processing until {format_time(end_sec)}")
    print(f"[info] Sampling 1 frame per {args.interval} frames (~{fps/args.interval:.1f} samples/sec)")

    frame_idx = start_frame
    raw_records = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        timestamp_sec = frame_idx / fps
        if end_sec is not None and timestamp_sec > end_sec:
            break
        if frame_idx % args.interval == 0:
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hit_list = detect_ui_one_frame(frame_gray, templates, args.threshold)
            scene_type = classify_by_tags(hit_list, templates)
            raw_records.append({
                "frame": frame_idx,
                "time_sec": round(timestamp_sec, 2),
                "scene": scene_type,
                "hit_ui": ",".join(hit_list) if hit_list else "",
            })
        frame_idx += 1
    cap.release()

    processed_frames = frame_idx - start_frame
    print(f"[info] Processed {processed_frames} frames, sampled {len(raw_records)} frames")

    # Temporal smoothing
    smooth_recs = smooth_records(raw_records, args.smooth)

    # Build segments
    segments = build_segments(smooth_recs)

    # Write simple CSV: time_range -> scene
    out_dir = os.path.dirname(args.output) or "."
    os.makedirs(out_dir, exist_ok=True)

    with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["start_time", "end_time", "scene"])
        writer.writeheader()
        for seg in segments:
            writer.writerow({
                "start_time": format_time(seg["start_time"]),
                "end_time": format_time(seg["end_time"]),
                "scene": seg["scene"],
            })
    print(f"[done] Result: {args.output}")

    # Console output: simple timeline
    print("\n===== Scene Timeline =====")
    for seg in segments:
        print(f"{format_time(seg['start_time'])} - {format_time(seg['end_time'])}  ->  {seg['scene']}")


if __name__ == "__main__":
    main()
