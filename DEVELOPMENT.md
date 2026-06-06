# Development Guide

This repository is now centered on a local DJI aerial-video processing workflow,
with a static GitHub Pages demo and two secondary browser experiments.

## Project Surfaces

- `ai_video_processor.py` is the main product workflow.
- `AI_VIDEO_PROCESSOR.md` is the operator guide for local processing.
- `index.html` is the static demo page for the product positioning.
- `README.md` is the product README and GitHub entry point.
- `simulation-simulator/` contains the Three.js drone simulator, now a secondary demo.
- `games/drone-game/` contains the Canvas obstacle game, now a secondary demo.
- `docs/` contains learning and safety material.

## Local Media Policy

`videos/` and `output/` are local-only folders:

- `videos/` contains source footage and optional same-name DJI `.SRT` files.
- `output/` contains generated frames, clips, scene lists, and JSON reports.
- Neither folder should be committed to GitHub.
- Do not commit API keys, original customer footage, exported clips, or private GPS data.

## Run The Static Site

From the repository root:

```bash
python -m http.server 8000
```

Then open:

- `http://localhost:8000/`
- `http://localhost:8000/simulation-simulator/`
- `http://localhost:8000/games/drone-game/`

The simulator uses CDN-hosted Three.js, so it needs network access the first
time those scripts are loaded.

## Run The Video Processor

Install dependencies:

```bash
pip install -r requirements.txt
```

Install FFmpeg, then choose an AI backend:

```powershell
# Default: local Ollama with LLaVA
ollama pull llava
$env:DJI_AI_BACKEND = "ollama"

# Optional cloud backends
$env:DJI_AI_BACKEND = "zhipuai"
$env:ZHIPUAI_API_KEY = "your_key"

$env:DJI_AI_BACKEND = "openai"
$env:OPENAI_API_KEY = "your_key"

$env:DJI_AI_BACKEND = "anthropic"
$env:ANTHROPIC_API_KEY = "your_key"
```

Useful local-only overrides:

```powershell
$env:DJI_VIDEO_DIR = "videos"
$env:DJI_OUTPUT_DIR = "output"
$env:DJI_NUM_FRAMES = "6"
$env:DJI_CLIP_DURATION = "5"
$env:DJI_ENABLE_AI_ANALYSIS = "0"
$env:DJI_ENABLE_SCENE_DETECTION = "0"
```

Run:

```bash
python ai_video_processor.py
```

## Scene Detection

PySceneDetect is optional because the base workflow should run with only
FFmpeg, Python, and the listed core dependencies.

```bash
pip install "scenedetect[opencv]>=0.6.4"
```

Enable it:

```powershell
$env:DJI_ENABLE_SCENE_DETECTION = "1"
$env:DJI_ENABLE_SCENE_CLIPS = "1"
```

If the package is not installed, `scene_detection.error` should explain the
missing dependency without blocking metadata, frame, clip, or SRT processing.

## Verification Checklist

Before publishing changes, run:

```bash
python -m py_compile ai_video_processor.py examples/python/drone_control.py
git diff --check
```

Safe no-input test:

```powershell
$env:DJI_VIDEO_DIR = "$env:TEMP\dji-empty-videos"
$env:DJI_OUTPUT_DIR = "$env:TEMP\dji-empty-output"
$env:DJI_ENABLE_AI_ANALYSIS = "0"
python ai_video_processor.py
```

Safe no-SRT processing test can use a tiny generated video in a temp folder:

```powershell
ffmpeg -f lavfi -i testsrc=size=320x180:rate=10 -t 1 -pix_fmt yuv420p "$env:TEMP\dji-sample-videos\DJI_TEST.MP4"
$env:DJI_VIDEO_DIR = "$env:TEMP\dji-sample-videos"
$env:DJI_OUTPUT_DIR = "$env:TEMP\dji-sample-output"
$env:DJI_ENABLE_AI_ANALYSIS = "0"
python ai_video_processor.py
```

Static-page smoke test:

```bash
python -m http.server 8000
```

Then verify:

- Home page renders the "DJI 航拍视频 AI 处理工作台" positioning.
- `AI_VIDEO_PROCESSOR.md` is linked from the home page.
- Simulator and game links still open.
- No obvious layout overlap on desktop and mobile widths.

## Deployment

The GitHub Pages demo is static and does not run the Python processor. It
explains the local workflow and links to the operator docs. No build step is
required for Pages.

Current intended deployment shape:

- Source: GitHub Pages from the active `codex/` branch root.
- Demo URL: `http://kevinten.com/dji/`
- Local processor: run on the user's machine, not on GitHub Pages.
