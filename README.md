# 🚁 DJI 无人机项目

> 探索无人机的无限可能！包含教程、3D模拟器、游戏和创意项目。

[![GitHub stars](https://img.shields.io/github/stars/kevinten10/dji)](https://github.com/kevinten10/dji/stargazers)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ⚡ 快速导航

| 你想做什么？ | 点击直达 |
|------------|---------|
| 🚀 体验3D模拟器 | `simulation/drone-simulator/index.html` |
| 🎮 玩躲避游戏 | `games/drone-game/index.html` |
| 📖 学习飞行 | [新手入门指南](docs/tutorials/beginner-guide.md) |
| ⚠️ 了解安全规则 | [安全飞行指南](docs/tutorials/safety-guide.md) |
| 💡 提升飞行技巧 | [实用飞行技巧](docs/tips/flight-tips.md) |
| 💻 Python编程 | [drone_control.py](examples/python/drone_control.py) |

---

## 🎮 立即体验

> ⚠️ **在线体验**：CloudBase部署待完成。请先下载项目到本地体验：
> ```bash
> git clone https://github.com/kevinten10/dji.git
> ```
> 然后用浏览器直接打开以下文件即可运行！

### 3D无人机模拟器
**浏览器中体验真实飞行！**

```
控制键：
W / S      → 上升 / 下降
A / D      → 左旋 / 右旋
↑ / ↓      → 前进 / 后退
← / →      → 左移 / 右移
R          → 重置位置
鼠标拖拽   → 旋转视角
滚轮       → 缩放视角
```

👉 打开 `simulation/drone-simulator/index.html`

---

### 无人机躲避游戏
**操控无人机躲避障碍物，看你能飞多远！**

```
控制键：
↑ ↓ ← → 或 WASD  → 控制飞行方向
```

👉 打开 `games/drone-game/index.html`

---

## 📋 无人机法规速查（2026年最新）

> ⚠️ **重要**：2026年是无人机监管升级关键年，请务必了解以下规定！

### 必须知道的核心法规

| 法规/标准 | 生效时间 | 要点 |
|----------|---------|------|
| 《无人驾驶航空器飞行管理暂行条例》 | 2024年1月1日 | 首部无人机专项行政法规 |
| 新《治安管理处罚法》 | 2026年1月1日 | 违规飞行将受处罚 |
| GB 46761—2025 实名登记国标 | 2025年12月 | 强制实名+激活要求 |
| GB 46750—2025 运行识别国标 | 2025年12月 | 无人机需广播识别信息 |

### 关键规定速记

```
📋 实名登记
├── 250克以上无人机必须登记
├── 网址：uom.caac.gov.cn（民用无人驾驶航空器综合管理平台）
└── 登记后获得登记号，粘贴于机身

🎓 操控资质
├── 微型（<250g）：免证飞行
├── 轻型：无需执照，但需了解规则
├── 中型/大型：需考取CAAC无人机执照
└── 培训：找AOPA认证培训机构

🚀 飞行规则
├── 120米高度限制（真高）
├── 远离机场、军事禁区、人口密集区
├── 需实名、报备空域（重要区域）
├── 购买第三方责任险（建议）
└── 2026年起部分区域需"飞手证"

🔴 禁飞区
├── 机场净空保护区
├── 军事禁区
├── 铁路、电力设施周边
├── 核电站、监管场所等
└── 查询：UOM平台的空域查询功能
```

### 违规处罚（2026年起）

| 违规行为 | 处罚 |
|---------|------|
| 黑飞（未实名） | 罚款、没收无人机 |
| 伤人/损物 | 民事赔偿 + 可能的刑事责任 |
| 闯入禁飞区 | 罚款，严重者拘留 |

📖 **详细法规**：[安全飞行指南](docs/tutorials/safety-guide.md)

---

## 📚 学习路径

### 🟢 新手入门
1. [新手入门指南](docs/tutorials/beginner-guide.md) → 了解无人机基础
2. [安全飞行指南](docs/tutorials/safety-guide.md) → 必须了解的安全规则

### 🟡 技能提升
3. [实用飞行技巧](docs/tips/flight-tips.md) → 航拍 + 飞行的实战技巧

### 🔴 创意拓展
4. [有趣项目创意](docs/ideas/fun-projects.md) → 游戏、摄影、编程、艺术灵感

---

## 📁 项目结构

```
dji/
├── simulation/drone-simulator/   🚁 3D无人机模拟器 (Three.js)
├── games/drone-game/             🎮 无人机躲避游戏
├── docs/
│   ├── tutorials/                📖 教程
│   │   ├── beginner-guide.md     新手入门
│   │   └── safety-guide.md       安全指南（含最新法规）
│   ├── tips/
│   │   └── flight-tips.md         飞行技巧
│   └── ideas/
│       └── fun-projects.md       创意灵感
└── examples/python/
    └── drone_control.py          🐍 Python控制示例
```

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| 3D渲染 | Three.js |
| 游戏 | JavaScript + Canvas |
| 示例代码 | Python |
| 文档 | Markdown |

---

## ⚠️ 安全与法律声明

> 🚨 **安全第一！合法飞行！**

无论是否使用模拟器，正式飞行时请：
- ✅ 在 [UOM平台](https://uom.caac.gov.cn) 完成实名登记
- ✅ 飞行前查询并遵守空域限制
- ✅ 250g以上必登记，商用需执照
- ✅ 远离机场、军事设施、人群
- ✅ 保持无人机在视距范围内 (VLOS)
- ✅ 建议购买第三方责任险
- ✅ 查看 [安全飞行指南](docs/tutorials/safety-guide.md)

---

## 🚀 部署到云端

如需将游戏部署到可在线访问：

### 方式1: CloudBase 静态托管
```bash
# 安装腾讯云CLI后
tcb hosting deploy ./simulation/drone-simulator
tcb hosting deploy ./games/drone-game
```

### 方式2: Vercel / Netlify
```bash
npm i -g vercel
vercel --prod
```

### 方式3: GitHub Pages
项目已开源，可直接fork到你的GitHub，启用Pages即可。

---

## 📝 许可证

MIT License - 欢迎 fork、star 和贡献！

---

*项目已开源至 [GitHub](https://github.com/kevinten10/dji)*
