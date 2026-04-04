# DJI Project Workspace

## Project Overview

这是一个专注于DJI大疆无人机的学习和创意项目。包含教程、3D模拟器、游戏和有趣的无人机相关项目。

## Directory Structure

```
dji/
├── docs/                      # 文档目录
│   ├── tutorials/             # 教程
│   │   ├── beginner-guide.md  # 新手入门指南
│   │   └── safety-guide.md    # 安全飞行指南
│   ├── tips/                  # 飞行技巧
│   │   └── flight-tips.md     # 实用飞行技巧
│   └── ideas/                 # 创意灵感
│       └── fun-projects.md    # 有趣项目创意
├── simulation/                # 3D模拟器
│   └── drone-simulator/       # Three.js无人机模拟器
│       ├── index.html
│       └── main.js
├── games/                     # 游戏项目
│   └── drone-game/            # 无人机躲避游戏
│       ├── index.html
│       └── main.js
├── examples/                  # 代码示例
│   └── python/                # Python示例
│       └── drone_control.py   # 无人机控制示例
├── README.md                  # 项目主文档
└── GEMINI.md                  # AI交互指南
```

## 已包含内容

### 教程 (docs/tutorials/)
- **beginner-guide.md** - 新手入门：无人机类型、关键术语、首次飞行准备、基本操作
- **safety-guide.md** - 安全飞行：法规要求、起飞前检查清单、紧急处理、天气限制

### 飞行技巧 (docs/tips/)
- **flight-tips.md** - 航拍技巧、飞行技巧、设备优化、创意技巧

### 创意项目 (docs/ideas/)
- **fun-projects.md** - 游戏与模拟、创意摄影、编程项目、实用项目、艺术创作等创意灵感

### 3D模拟器 (simulation/drone-simulator/)
使用Three.js构建的3D无人机飞行模拟器，支持：
- WASD/方向键控制飞行
- 鼠标拖拽旋转视角
- 实时遥测数据显示（高度、速度、位置、姿态）
- 模拟建筑物和树木环境

打开 `index.html` 即可体验。

### 无人机躲避游戏 (games/drone-game/)
一个有趣的无人机躲避障碍物游戏，支持：
- 方向键/WASD控制
- 分数和等级系统
- 多种障碍物类型（建筑物、小鸟、敌方无人机）
- 3条生命值

打开 `index.html` 开始游戏。

### Python控制示例 (examples/python/)
- **drone_control.py** - 无人机控制基类，支持起飞、降落、移动、旋转等操作
- 包含路径规划辅助函数

## AI Guidelines

当与此项目交互时，AI agents应该：
- 遵循现有目录结构
- 重视安全，始终强调飞行安全
- 帮助扩展教程、添加新示例或创建新项目
- 保持代码简洁、可运行
