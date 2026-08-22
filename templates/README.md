# UI 模板准备指南

## 模板一览

脚本目前内置 **battle（战斗）> story（剧情）** 的优先级，未命中任何模板时归类为 **unknown**。
**缺少的模板会自动跳过**（不报错），你可以逐步补充。

### 剧情场景 (story)

| 文件名 | 说明 | 截图区域 |
|--------|------|---------|
| `skip_button.png` | 左上角六边形跳过按钮 | 左上角 |
| `story_ui_top.png` | 右上角剧情模式按钮（记录/暂停/关闭UI） | 右上角 |
| `dialog.png` | 对话框（如果有实体底色） | 底部对话区域（可选） |

> 鸣潮对话框为透明背景，因此优先使用**左上角跳过按钮 + 右上角剧情按钮**作为稳定特征，而非对话框本身。

### 战斗场景 (battle)

| 文件名 | 说明 | 鸣潮中的位置 |
|--------|------|-------------|
| `player_hp.png` | 玩家血条 | 左下角角色头像旁 |
| `enemy_hp.png` | 敌人/Boss血条 | 敌人头顶或屏幕上方 |
| `skill_bar.png` | 技能/共鸣技能栏 | 右下角 |

## 扩展场景（当前代码未启用）

以下场景类别已在上层 `SCENE_PRIORITY` 中预留了优先级，但 **`UI_CONFIG` 尚未包含对应模板条目**，需要自行在 `scripts/scene_recognize.py` 的 `UI_CONFIG` 中添加后才会生效：

| 场景 | 可添加的模板 | 说明 |
|------|-------------|------|
| `exploration` | `minimap.png`、`quest_tracker.png` | 小地图 / 任务追踪 |
| `menu` | `map_window.png`、`menu_tab.png` | 大地图窗口 / 菜单标签 |

## 截图要求

1. **分辨率一致**：模板必须与视频中 UI 显示的分辨率一致
2. **内容精简**：只截取 UI 元素本身，不要多余背景
3. **格式**：PNG（推荐）或 JPG
4. **命名严格**：文件名必须与上表完全一致
5. **放入 `templates/` 目录**

## 快速验证

放好模板后，运行脚本时会显示加载了哪些模板：

```
[info] Loaded 6 UI templates from ./templates
       battle: player_hp, enemy_hp, skill_bar
       story: skip_button, story_ui_top, dialog
[warn] Skipped 0 missing templates
```

这表示缺少的模板已被跳过，不影响已有模板的识别。
