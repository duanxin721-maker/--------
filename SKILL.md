---
name: game-video-scene-recognize
description: "Game video scene classification based on UI template matching. Classifies video segments as story (cutscene/dialogue) or battle (combat) by detecting predefined UI elements. Outputs a simple scene timeline (CSV)."
agent_created: true
---

# Game Video Scene Recognize

## What It Does

Analyzes a game video and classifies each time segment as:
- **`story`** — cutscene, dialogue, or cinematic
- **`battle`** — combat with HP bars and skill UI
- **`unknown`** — no recognizable UI features

**Approach:** OpenCV template matching on predefined UI screenshots + simple priority rules. No AI training required.

---

## Quick Start (For Interviewer)

### 1. Install
```bash
pip install opencv-python
```

### 2. Prepare Templates
From the game video, screenshot these UI elements and save to `templates/`:

| File | What to Screenshot |
|------|-------------------|
| `skip_button.png` | Top-left skip button (story mode) |
| `story_ui_top.png` | Top-right buttons cluster (story mode) |
| `dialog.png` | Bottom dialog text box (story mode) |
| `player_hp.png` | Player health bar (battle mode) |
| `enemy_hp.png` | Enemy/boss health bar (battle mode) |
| `skill_bar.png` | Skill icons bar (battle mode) |

**Tip:** Crop tightly around the UI element only. Avoid extra background.

### 3. Place Video
```bash
cp your_video.mp4 input.mp4
```

### 4. Run
```bash
# Analyze entire video
python scripts/scene_recognize.py

# Analyze specific time range
python scripts/scene_recognize.py --start 1:00:00 --end 1:08:00

# Adjust sensitivity
python scripts/scene_recognize.py --threshold 0.5 --interval 30
```

### 5. Check Output
**Console:**
```
===== Scene Timeline =====
1:00:00 - 1:02:55  ->  story
1:02:56 - 1:03:00  ->  unknown
1:03:01 - 1:07:59  ->  story
```

**CSV file** (`output_scene_result.csv`):
```csv
start_time,end_time,scene
1:00:00,1:02:55,story
1:02:56,1:03:00,unknown
1:03:01,1:07:59,story
```

---

## How It Works

1. **Frame Sampling** — reads video, samples 1 frame every N frames (default N=30 @30fps = 1/sec)
2. **Template Matching** — runs OpenCV `matchTemplate` against each UI screenshot
3. **Rule Classification** — `battle` templates have priority over `story` templates
4. **Temporal Smoothing** — ignores single-frame flips; confirms scene change after 3 consecutive frames

---

## Parameters

| Flag | Default | Description |
|------|---------|-------------|
| `--video` | `input.mp4` | Input video path |
| `--templates` | `./templates` | Template directory |
| `--output` | `output_scene_result.csv` | Output CSV path |
| `--threshold` | `0.7` | Match threshold (0-1, higher = stricter) |
| `--interval` | `30` | Sample 1 frame per N frames |
| `--smooth` | `3` | Frames needed to confirm scene change |
| `--start` | `0` | Start time (MM:SS or HH:MM:SS) |
| `--end` | `end` | End time (MM:SS or HH:MM:SS) |

---

## Project Structure

```
game-video-scene-recognize/
├── scripts/
│   └── scene_recognize.py    # Main script
├── templates/                # UI templates (user-provided)
│   ├── skip_button.png
│   ├── story_ui_top.png
│   ├── dialog.png
│   ├── player_hp.png
│   ├── enemy_hp.png
│   └── skill_bar.png
├── input.mp4                 # Video to analyze
├── output_scene_result.csv   # Generated result
├── requirements.txt          # Python dependencies
└── README.md                 # Full documentation
```
