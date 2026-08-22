# UI 模板准备指南

## 模板一览

脚本按**场景优先级**识别：menu > battle > story > exploration > unknown。
**缺少的模板会自动跳过**（不报错），你可以逐步补充。

### 剧情场景 (story) — 已自动生成 2 个

| 文件名 | 说明 | 截图区域 |
|--------|------|---------|
| `skip_button.png` | 左上角六边形跳过按钮 | 已从你的截图自动裁剪 |
| `story_ui_top.png` | 右上角剧情模式按钮（记录/暂停/关闭UI） | 已从你的截图自动裁剪 |
| `dialog.png` | 对话框（如果有实体底色） | 可选，底部对话区域 |

> 鸣潮对话框为透明背景，因此使用**左上角跳过按钮 + 右上角剧情按钮**作为稳定特征，而非对话框本身。

### 战斗场景 (battle) — 需要你截图

| 文件名 | 说明 | 鸣潮中的位置 |
|--------|------|-------------|
| `player_hp.png` | 玩家血条 | 左下角角色头像旁 |
| `enemy_hp.png` | 敌人/Boss血条 | 敌人头顶或屏幕上方 |
| `skill_bar.png` | 技能/共鸣技能栏 | 右下角 |

### 探索场景 (exploration) — 需要你截图

| 文件名 | 说明 | 鸣潮中的位置 |
|--------|------|-------------|
| `minimap.png` | 小地图 | 右上角 |
| `quest_tracker.png` | 任务追踪（可选） | 左侧 |

### 菜单场景 (menu) — 可选

| 文件名 | 说明 |
|--------|------|
| `map_window.png` | 大地图窗口（打开地图时出现） |
| `menu_tab.png` | 菜单标签栏 |

## 截图要求

1. **分辨率一致**：模板必须与视频中 UI 显示的分辨率一致
2. **内容精简**：只截取 UI 元素本身，不要多余背景
3. **格式**：PNG（推荐）或 JPG
4. **命名严格**：文件名必须与上表完全一致
5. **放入 `templates/` 目录**

## 快速验证

放好模板后，运行脚本时会显示加载了哪些模板：

```
[info] Loaded 5 UI templates from ./templates
       story: skip_button, story_ui_top
       battle: player_hp, skill_bar
       exploration: minimap
[warn] Skipped 5 missing templates: enemy_hp.png, dialog.png, ...
```

这表示缺少的模板已被跳过，不影响已有模板的识别。
