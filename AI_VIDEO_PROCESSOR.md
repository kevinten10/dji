# DJI Footage Copilot 使用指南

这是本项目的主功能文档。`ai_video_processor.py` 面向 DJI 航拍素材的本地处理：扫描视频、读取元信息、解析同名 SRT 遥测、抽取关键帧、生成预切片、可选场景检测、调用 AI 视觉后端，并输出剪辑与发布建议。

## 你能得到什么

- `analysis.json`：单条视频的完整结构化分析。
- `report.json`：批量处理总报告。
- `frames/`：用于人工筛片和 AI 分析的均匀关键帧。
- `clips/`：固定秒数预切片，可选场景切片。
- `scenes.json`：启用 PySceneDetect 后的场景边界列表。
- `publish_package`：推荐发布格式、剪辑注意点、标签方向。
- `generated_script`：AI 生成的标题、描述、标签、音乐氛围和剪辑计划。

## 安装

### 1. FFmpeg

Windows:

```bash
winget install ffmpeg
```

macOS:

```bash
brew install ffmpeg
```

Linux:

```bash
sudo apt install ffmpeg
```

安装后确认：

```bash
ffmpeg -version
ffprobe -version
```

### 2. Python 依赖

```bash
pip install -r requirements.txt
```

### 3. AI 后端

默认是本地 Ollama，不需要 API Key：

```bash
ollama pull llava
ollama serve
```

可选云端后端：

```powershell
$env:DJI_AI_BACKEND = "zhipuai"
$env:ZHIPUAI_API_KEY = "your_key"

$env:DJI_AI_BACKEND = "openai"
$env:OPENAI_API_KEY = "your_key"

$env:DJI_AI_BACKEND = "anthropic"
$env:ANTHROPIC_API_KEY = "your_key"
```

密钥只通过本机环境变量读取，不要写入仓库。

## 基本使用

### 没有素材：先跑内置 demo

第一次使用推荐先跑 demo。脚本会生成一个小的 `DJI_SAMPLE.MP4` 和同名 `DJI_SAMPLE.SRT`，并在不调用 AI 的情况下跑完整工作流：

```bash
python ai_video_processor.py --create-sample
```

你会看到：

```text
videos/DJI_SAMPLE.MP4
videos/DJI_SAMPLE.SRT
output/DJI_SAMPLE/analysis.json
output/report.json
```

这个 demo 只需要 FFmpeg/FFprobe，不需要 Ollama 或 API Key。

### 有真实素材：放入 videos/

把视频放进 `videos/`：

```text
videos/
├── DJI_0001.MP4
├── DJI_0001.SRT
└── DJI_0002.MOV
```

运行：

```bash
python ai_video_processor.py --no-ai
```

支持视频扩展名：

- `.mp4`
- `.mov`
- `.avi`
- `.mkv`

脚本只扫描视频文件，同名 `.SRT` 会作为 sidecar 遥测文件自动读取。

开启 AI 分析：

```bash
python ai_video_processor.py --with-ai
```

## 推荐的首次本地测试

如果还没有真实素材，可以先测试安全路径：

```powershell
$env:DJI_VIDEO_DIR = "$env:TEMP\dji-empty-videos"
$env:DJI_OUTPUT_DIR = "$env:TEMP\dji-empty-output"
$env:DJI_ENABLE_AI_ANALYSIS = "0"
python ai_video_processor.py
```

没有素材时脚本会写出一个空的 `report.json`，不会报错退出。

## 配置项

| 环境变量 | 作用 | 默认值 |
| --- | --- | --- |
| `DJI_VIDEO_DIR` | 输入视频目录 | `./videos` |
| `DJI_OUTPUT_DIR` | 输出目录 | `./output` |
| `DJI_AI_BACKEND` | AI 后端：`ollama`、`zhipuai`、`openai`、`anthropic` | `ollama` |
| `DJI_OLLAMA_URL` | Ollama 服务地址 | `http://localhost:11434` |
| `DJI_OLLAMA_MODEL` | Ollama 视觉模型 | `llava` |
| `DJI_NUM_FRAMES` | 每个视频均匀抽帧数量 | `6` |
| `DJI_CLIP_DURATION` | 固定切片时长，单位秒 | `5` |
| `DJI_ENABLE_AI_ANALYSIS` | 是否调用 AI 分析帧 | `true` |
| `DJI_ENABLE_AUTO_EDIT` | 是否生成预切片 | `true` |
| `DJI_ENABLE_SCENE_DETECTION` | 是否运行 PySceneDetect | `false` |
| `DJI_ENABLE_SCENE_CLIPS` | 是否为检测到的场景导出片段 | `false` |
| `DJI_SCENE_THRESHOLD` | PySceneDetect 内容检测阈值 | `27.0` |

等价 CLI 参数：

| 参数 | 作用 |
| --- | --- |
| `--create-sample` | 生成并处理内置 demo 视频和 SRT |
| `--video-dir <path>` | 指定输入目录 |
| `--output-dir <path>` | 指定输出目录 |
| `--no-ai` | 关闭 AI，只做本地整理 |
| `--with-ai` | 启用 AI 分析 |
| `--backend ollama` | 指定 AI 后端 |
| `--frames 4` | 指定抽帧数量 |
| `--clip-duration 8` | 指定固定切片秒数 |
| `--scene-detect` | 启用 PySceneDetect |
| `--scene-clips` | 可用时导出场景片段 |

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
        ├── clip_001.mp4
        └── scenes/
            └── scene_001.mp4
```

### `analysis.json` 关键字段

```json
{
  "workflow_version": "3.0.0",
  "video": {
    "duration_seconds": 52.4,
    "width": 3840,
    "height": 2160,
    "codec": "hevc",
    "fps": 29.97,
    "size_mb": 812.31
  },
  "telemetry": {
    "exists": true,
    "cue_count": 1200,
    "fields_detected": ["latitude", "longitude", "relative_altitude", "gimbal_pitch"],
    "stats": {}
  },
  "scene_detection": {
    "enabled": false,
    "available": false,
    "scenes": []
  },
  "publish_package": {
    "recommended_formats": ["YouTube/Bilibili 16:9", "website hero background"],
    "editing_notes": []
  }
}
```

## DJI SRT 遥测

脚本会寻找与视频同名的 `.SRT`、`.srt` 或 `.Srt`：

```text
DJI_0420.MP4
DJI_0420.SRT
```

解析器会尽量提取：

- `latitude` / `longitude`
- `relative_altitude` / `absolute_altitude` / `altitude`
- `speed`
- `gimbal_pitch` / `gimbal_yaw` / `gimbal_roll`
- `iso` / `shutter` / `f_number` / `ev`
- `color_temperature` / `focal_length`

不同 DJI 机型和 App 版本的 SRT 文本格式可能不同，所以当前实现保留 `samples[].text` 原文片段，并把解析逻辑集中在 `DJI_SRT_FIELD_PATTERNS`，方便继续扩展。

## PySceneDetect 场景检测

安装可选依赖：

```bash
pip install "scenedetect[opencv]>=0.6.4"
```

启用：

```powershell
$env:DJI_ENABLE_SCENE_DETECTION = "1"
python ai_video_processor.py
```

如需把场景边界也导出成片段：

```powershell
$env:DJI_ENABLE_SCENE_CLIPS = "1"
```

如果没有安装 PySceneDetect，脚本会在 `scene_detection.error` 里写明原因，不会阻断普通抽帧和固定切片。

## 关闭 AI，仅做本地素材整理

```powershell
$env:DJI_ENABLE_AI_ANALYSIS = "0"
python ai_video_processor.py
```

这会保留 FFprobe、SRT、抽帧、切片、场景检测和报告输出，适合没有 Ollama 或 API Key 时做基础整理。

## 常见问题

### FFmpeg not found

确认 `ffmpeg -version` 和 `ffprobe -version` 都能运行。Windows 推荐使用 `winget install ffmpeg`。

### Ollama 无法连接

确认已执行：

```bash
ollama pull llava
ollama serve
```

也可以临时关闭 AI：

```powershell
$env:DJI_ENABLE_AI_ANALYSIS = "0"
```

### 没有 SRT

可以正常处理视频。`telemetry.exists` 会是 `false`，发布建议会说明没有遥测信息。

### PySceneDetect 未安装

可以正常处理视频。安装 `scenedetect[opencv]` 后再打开 `DJI_ENABLE_SCENE_DETECTION`。

### output 和 videos 是否会提交到 GitHub

不会。`videos/` 和 `output/` 是本地素材与生成物目录，已经在 `.gitignore` 中忽略。

## 示例与 Skill

- [examples/README.md](examples/README.md)：示例 SRT、示例报告和 demo 命令。
- [examples/sample-dji-srt/DJI_SAMPLE.SRT](examples/sample-dji-srt/DJI_SAMPLE.SRT)：可读的 DJI 风格 SRT 样例。
- [examples/sample-output/report.example.json](examples/sample-output/report.example.json)：批量报告输出结构样例。
- [docs/skills/dji-footage-copilot/SKILL.md](docs/skills/dji-footage-copilot/SKILL.md)：给 Codex/AI 代理复用的项目 skill。
