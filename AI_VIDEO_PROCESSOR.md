# DJI 无人机视频 AI 全自动处理工具

本工具基于 **FFmpeg + Python + 多 AI 视觉后端**，用于本地批量处理航拍视频：提取关键帧、自动切分片段、调用 AI 分析画面，并生成标题、文案、标签和音乐氛围建议。

## 功能特点

- **多 AI 后端**：默认使用本地 Ollama/LLaVA，也可切换智谱 AI、OpenAI、Anthropic。
- **视频信息读取**：通过 FFprobe 获取时长、尺寸、编码和分辨率。
- **关键帧提取**：按视频时长均匀抽取帧图片，用于视觉分析。
- **自动切片**：按固定时长将原始视频拆分为多个片段。
- **AI 文案生成**：基于帧分析生成中文标题、描述、标签和音乐风格建议。
- **批量处理**：自动扫描 `videos/` 下的视频文件并输出结构化报告。

## 安装

### 1. 安装 FFmpeg

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

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 选择 AI 后端

默认后端是 `ollama`，不需要 API Key，但需要本机安装并启动 Ollama：

```bash
ollama pull llava
ollama serve
```

也可以通过环境变量切换云端后端：

```bash
# 智谱 AI
set DJI_AI_BACKEND=zhipuai
set ZHIPUAI_API_KEY=你的密钥

# OpenAI
set DJI_AI_BACKEND=openai
set OPENAI_API_KEY=你的密钥

# Anthropic
set DJI_AI_BACKEND=anthropic
set ANTHROPIC_API_KEY=你的密钥
```

PowerShell 可使用：

```powershell
$env:DJI_AI_BACKEND = "ollama"
```

## 使用方法

将本地视频放入 `videos/`，然后运行：

```bash
python ai_video_processor.py
```

支持的视频扩展名包括：

- `.mp4`
- `.mov`
- `.avi`
- `.mkv`

## 配置

可以编辑脚本中的 `CONFIG`，也可以用环境变量覆盖常用配置：

| 环境变量 | 含义 | 默认值 |
| --- | --- | --- |
| `DJI_AI_BACKEND` | AI 后端：`ollama`、`zhipuai`、`openai`、`anthropic` | `ollama` |
| `DJI_OLLAMA_URL` | Ollama 服务地址 | `http://localhost:11434` |
| `DJI_OLLAMA_MODEL` | Ollama 视觉模型 | `llava` |
| `DJI_VIDEO_DIR` | 输入视频目录 | `./videos` |
| `DJI_OUTPUT_DIR` | 输出目录 | `./output` |
| `DJI_NUM_FRAMES` | 每个视频提取帧数 | `6` |
| `DJI_CLIP_DURATION` | 切片时长，单位秒 | `5` |
| `DJI_QUALITY` | FFmpeg 质量参数，数值越低质量越高 | `23` |

## 处理流程

```text
videos/*.MP4
    |
    v
FFprobe 读取视频信息
    |
    v
FFmpeg 均匀提取关键帧
    |
    v
AI 后端逐帧分析画面
    |
    v
AI 生成标题、描述、标签、音乐建议
    |
    v
FFmpeg 切分视频片段
    |
    v
output/<video_name>/analysis.json
output/<video_name>/frames/
output/<video_name>/clips/
output/report.json
```

## 输出内容

```text
output/
├── DJI_0392/
│   ├── frames/
│   │   ├── frame_001.jpg
│   │   └── ...
│   ├── clips/
│   │   ├── clip_000.mp4
│   │   └── ...
│   └── analysis.json
├── DJI_0405/
│   └── ...
└── report.json
```

`videos/` 和 `output/` 是本地素材与生成结果，已加入 `.gitignore`，避免误提交大文件。

## 常见问题

### 提示 FFmpeg not found

请先安装 FFmpeg，并确认 `ffmpeg -version` 和 `ffprobe -version` 可在终端中运行。

### Ollama 无法连接

确认 Ollama 已安装、已启动，并且模型已下载：

```bash
ollama pull llava
ollama serve
```

### 云端后端提示 API Key not set

确认已设置对应环境变量：

- 智谱 AI：`ZHIPUAI_API_KEY`
- OpenAI：`OPENAI_API_KEY`
- Anthropic：`ANTHROPIC_API_KEY`

### zhipuai、openai 或 anthropic 包未安装

这些 SDK 是可选依赖。仅在使用对应后端时需要安装：

```bash
pip install zhipuai openai anthropic
```

当前脚本中的 OpenAI 和 Anthropic 调用直接使用 HTTP API，因此基础运行只需要 `requests`。
`requirements.txt` 也约束了 `chardet<6`，用于避免部分全局 Python 环境中 `requests` 的字符集兼容警告。

## 验证

```bash
python -m py_compile ai_video_processor.py
python ai_video_processor.py
```

如果不希望实际调用 AI，可临时将脚本中的 `enable_ai_analysis` 设为 `False`，或保持 Ollama 未启动观察错误处理。

## 许可证

MIT License。详见 `LICENSE`。
