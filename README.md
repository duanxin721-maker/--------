# Game Video Scene Recognize

基于 OpenCV 模板匹配 + 预设业务规则的游戏视频场景划分工具。无需训练任何深度学习模型，即可对固定 UI 风格的游戏视频进行剧情/战斗场景识别。

## 核心思路

- **固定游戏** = UI 风格和布局恒定，可作为可靠的检测特征
- **完全可解释**：每个分类都能追溯到匹配到的 UI 模板
- **易于迭代**：增删模板或规则即可，无需重新训练
- **低算力、高速度**

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备 UI 模板

从目标游戏视频中截取 UI 模板，放入 `templates/` 目录：

| 模板文件 | 内容 | 场景类别 |
|---------|------|---------|
| `skip_button.png` | 左上角剧情跳过键 | story |
| `story_ui_top.png` | 右上角剧情按钮组 | story |
| `dialog.png` | 底部剧情对话框 | story |
| `player_hp.png` | 玩家血条 | battle |
| `enemy_hp.png` | 敌人/BOSS血条 | battle |
| `skill_bar.png` | 右下角技能栏 | battle |

**截图要点**：只截 UI 元素本身，避免多余背景，保持和视频中的分辨率一致。

### 3. 放置视频

将待分析的视频重命名为 `input.mp4`，放在项目根目录。

### 4. 运行识别

```bash
# 分析整个视频
python scripts/scene_recognize.py

# 分析指定时间段
python scripts/scene_recognize.py --start 1:00:00 --end 1:08:00

# 调整灵敏度（阈值越低越容易匹配）
python scripts/scene_recognize.py --threshold 0.5 --interval 30
```

## 输出结果

**控制台输出：**
```
===== Scene Timeline =====
1:00:00 - 1:02:55  ->  story
1:02:56 - 1:03:00  ->  unknown
1:03:01 - 1:07:59  ->  story
```

**CSV 文件**（`output_scene_result.csv`）：
```csv
start_time,end_time,scene
1:00:00,1:02:55,story
1:02:56,1:03:00,unknown
1:03:01,1:07:59,story
```

## 分类规则（优先级从高到低）

1. **battle**：检测到任何战斗 UI（血条/技能栏）→ `battle`（即使同时存在对话框）
2. **story**：无战斗 UI 但检测到剧情 UI（跳过键/对话框）→ `story`
3. **unknown**：以上皆非 → `unknown`（过场动画、加载画面等）

## 时序平滑

- 场景切换需 N 个连续采样帧一致才确认（默认 N=3）
- 孤立异常帧会被忽略，继承上一个有效场景
- 最终输出按时间段合并的场景分段

## 参数配置

| 参数 | 默认值 | 说明 |
|------|-------|------|
| `--video` | `input.mp4` | 输入视频路径 |
| `--templates` | `./templates` | 模板目录 |
| `--output` | `output_scene_result.csv` | 输出 CSV 路径 |
| `--threshold` | `0.7` | 模板匹配阈值（0-1，越高越严格） |
| `--interval` | `30` | 采样间隔帧数（30fps 下≈1秒/帧） |
| `--smooth` | `3` | 平滑窗口大小 |
| `--start` | `0` | 开始时间（MM:SS 或 HH:MM:SS） |
| `--end` | `视频结束` | 结束时间（MM:SS 或 HH:MM:SS） |

## 项目结构

```
game-video-scene-recognize/
├── README.md                 # 本文件
├── SKILL.md                  # TRAE Skill 定义文件
├── requirements.txt          # Python 依赖
├── .gitignore               # Git 忽略配置
├── scripts/
│   └── scene_recognize.py   # 主程序
├── templates/               # UI 模板（用户准备）
└── references/
    └── report_and_interview.md  # 面试报告要点
```

## 局限性 & 优化方向

- 模板匹配对 UI 缩放和位置漂移敏感；若游戏 UI 变化需重新截图
- 阈值过严会漏检，过松会误检，建议针对目标游戏微调
- 扩展方向：YOLO 检测 UI 组件、OCR 识别对话文本、多尺度模板匹配

---

*本项目为面试作业，采用纯规则方案实现可解释的视频场景识别。*
