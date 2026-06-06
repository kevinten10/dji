# DJI 航拍视频 AI 处理器

> DJI Footage Copilot：把无人机拍回来的 MP4/MOV 素材，变成可检索、可剪辑、可发布的结构化报告。

[![GitHub stars](https://img.shields.io/github/stars/kevinten10/dji)](https://github.com/kevinten10/dji/stargazers)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Static Demo](https://img.shields.io/badge/demo-GitHub%20Pages-blue.svg)](http://kevinten.com/dji/)

这个项目的核心价值不是“再做一个无人机教程页”，而是解决 DJI 航拍之后最耗时间的一步：素材整理、关键帧查看、片段预切、SRT 遥测读取、AI 画面分析、标题文案和发布建议生成。

## 适用场景

- 旅行或风光航拍：快速筛选一堆 DJI 视频里的高光片段。
- 短视频发布：生成标题、描述、标签、音乐氛围和剪辑顺序建议。
- 商业素材整理：按视频元信息、关键帧、片段和报告组织交付物。
- 后期前筛片：用 FFmpeg/FFprobe 和可选 PySceneDetect 建立第一轮剪辑依据。
- 遥测辅助判断：读取同名 DJI `.SRT`，保留 GPS、高度、速度、云台和相机参数扩展点。

## 工作流

```text
videos/DJI_0001.MP4
videos/DJI_0001.SRT
        |
        v
FFprobe 读取时长、分辨率、编码、帧率、码率、文件大小
        |
        v
DJI SRT 解析 GPS / 高度 / 速度 / 云台 / 相机参数
        |
        v
FFmpeg 均匀抽帧 + 固定时长切片
        |
        v
可选 PySceneDetect 场景检测
        |
        v
Ollama / 智谱 AI / OpenAI / Anthropic 分析画面
        |
        v
output/<video_name>/analysis.json
output/report.json
frames/ clips/ scenes.json publish copy
```

## 快速开始

1. 安装 FFmpeg，并确保 `ffmpeg -version` 和 `ffprobe -version` 可运行。

```bash
winget install ffmpeg
```

2. 安装 Python 依赖。

```bash
pip install -r requirements.txt
```

3. 准备本地 AI 后端。默认使用 Ollama，不需要 API Key。

```bash
ollama pull llava
ollama serve
```

4. 放入素材并运行。

```bash
mkdir videos
# 把 DJI_0001.MP4 / DJI_0001.SRT 放入 videos/
python ai_video_processor.py
```

支持 `.mp4`、`.mov`、`.avi`、`.mkv`，并会自动寻找同名 `.SRT` / `.srt` 作为 DJI 遥测文件。

## 输出结构

```text
output/
├── report.json
└── DJI_0001/
    ├── analysis.json
    ├── scenes.json
    ├── frames/
    │   ├── frame_001.jpg
    │   └── ...
    └── clips/
        ├── clip_000.mp4
        └── ...
```

`analysis.json` 会包含：

- `video`：时长、分辨率、编码、帧率、码率、文件大小。
- `telemetry`：同名 DJI SRT 的 cue 数量、字段列表、样本和统计值。
- `scene_detection`：PySceneDetect 是否启用、是否可用、场景列表。
- `frames`：均匀抽取的关键帧路径和时间点。
- `clips`：固定时长切片，以及可选场景切片。
- `frame_analyses`：AI 对关键帧的画面分析。
- `publish_package`：推荐发布格式、剪辑注意点、标签方向。
- `generated_script`：AI 生成的标题、描述、标签、音乐氛围和剪辑计划。

## 常用配置

通过环境变量即可切换输入输出、AI 后端和功能开关：

| 环境变量 | 含义 | 默认值 |
| --- | --- | --- |
| `DJI_VIDEO_DIR` | 输入素材目录 | `./videos` |
| `DJI_OUTPUT_DIR` | 输出目录 | `./output` |
| `DJI_AI_BACKEND` | `ollama`、`zhipuai`、`openai`、`anthropic` | `ollama` |
| `DJI_NUM_FRAMES` | 每个视频均匀抽帧数量 | `6` |
| `DJI_CLIP_DURATION` | 固定切片秒数 | `5` |
| `DJI_ENABLE_AI_ANALYSIS` | 是否启用 AI 视觉分析 | `true` |
| `DJI_ENABLE_AUTO_EDIT` | 是否生成 clips | `true` |
| `DJI_ENABLE_SCENE_DETECTION` | 是否启用 PySceneDetect | `false` |
| `DJI_ENABLE_SCENE_CLIPS` | 是否按场景生成片段 | `false` |

云端 AI 后端需要自行在本机设置密钥；项目不会写入、提交或展示任何 API Key。

## 可选能力

### PySceneDetect

固定秒数切片适合快速浏览，但真正剪辑更需要场景边界。安装可选依赖后启用：

```bash
pip install "scenedetect[opencv]>=0.6.4"
set DJI_ENABLE_SCENE_DETECTION=1
```

### DJI SRT 遥测

很多 DJI 视频旁边会有同名 `.SRT`，例如：

```text
DJI_0001.MP4
DJI_0001.SRT
```

当前解析器是宽松结构：优先提取 GPS、相对高度、绝对高度、速度、云台角度、ISO、快门、光圈、EV、色温、焦距等字段；如果某些机型格式不同，也会保留原始样本文本，方便继续扩展。

## 在线演示

- [GitHub Pages 首页](http://kevinten.com/dji/)：展示新的“航拍视频处理工作台”定位。
- [AI 视频处理主文档](AI_VIDEO_PROCESSOR.md)：完整命令、配置、输出结构和 FAQ。
- [3D 飞行模拟器](simulation-simulator/index.html)：保留为附加学习实验。
- [无人机躲避挑战](games/drone-game/index.html)：保留为附加互动演示。
- [开发与验证指南](DEVELOPMENT.md)：本地验证、静态部署和发布检查。

## 本地素材安全

`videos/` 和 `output/` 是本地素材与生成物目录，默认不提交 Git。请不要把原始视频、导出片段、API Key 或私密位置信息提交到 GitHub。

## 技术参考

- [FFmpeg / FFprobe documentation](https://www.ffmpeg.org/documentation.html)
- [PySceneDetect documentation](https://www.scenedetect.com/docs/latest/)
- [ExifTool geotagging documentation](https://www.exiftool.org/geotag.html)

## 路线图

- 更完整的 DJI SRT 机型兼容解析。
- 场景检测抽帧与高光片段评分。
- `report.html` 可视化报告导出。
- ExifTool 辅助地理信息和媒体元数据读取。
- 面向批量交付的素材索引和搜索。

## 许可证

MIT License，详见 [LICENSE](LICENSE)。
