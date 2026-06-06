# DJI Footage Copilot Workspace

## Project Overview

This repository is centered on a local DJI aerial-footage processing workflow.
The main value is turning DJI videos and same-name `.SRT` telemetry files into
structured reports, review frames, clips, scene lists, edit notes, and publish
copy. The 3D simulator, game, and learning docs are secondary supporting demos.

## Primary Workflow

Default first-run demo:

```bash
python ai_video_processor.py --create-sample
```

Real footage workflow:

```text
videos/DJI_0001.MP4
videos/DJI_0001.SRT
        |
        v
ai_video_processor.py
        |
        v
output/DJI_0001/analysis.json
output/report.json
```

Use `--no-ai` for private metadata/frame/clip/SRT processing. Use `--with-ai`
only after Ollama is running or a cloud API key has been configured locally.

## Directory Structure

```text
dji/
├── ai_video_processor.py                  # Main DJI footage processing workflow
├── AI_VIDEO_PROCESSOR.md                  # Operator guide
├── README.md                              # Product README
├── DEVELOPMENT.md                         # Local development and validation guide
├── docs/
│   ├── skills/dji-footage-copilot/        # Reusable AI-agent skill
│   ├── tutorials/                         # Learning and safety material
│   ├── tips/
│   └── ideas/
├── examples/
│   ├── sample-dji-srt/                    # Synthetic DJI-style SRT
│   ├── sample-output/                     # Example report shape
│   └── python/                            # Python drone-control example
├── simulation-simulator/                  # Secondary Three.js demo
├── games/drone-game/                      # Secondary Canvas demo
├── index.html                             # GitHub Pages product demo
└── requirements.txt
```

## AI Agent Guidelines

- Treat DJI footage and SRT telemetry as private local data.
- Do not commit `videos/`, `output/`, API keys, source media, generated clips, or private GPS data.
- Prefer `python ai_video_processor.py --create-sample` before asking the user for real footage.
- Prefer `--no-ai` for first validation, then `--with-ai` after the user chooses a backend.
- Keep README, `AI_VIDEO_PROCESSOR.md`, `DEVELOPMENT.md`, and `docs/skills/dji-footage-copilot/SKILL.md` aligned when commands or outputs change.
- The project should feel like a useful post-flight footage tool, not a generic drone tutorial site.
- Simulator and game work should stay secondary unless the user explicitly changes the product direction.

## Validation Commands

```bash
python -m py_compile ai_video_processor.py examples/python/drone_control.py
git diff --check
```

PowerShell sample validation:

```powershell
$demoVideoDir = Join-Path $env:TEMP "dji-demo-videos"
$demoOutputDir = Join-Path $env:TEMP "dji-demo-output"
python ai_video_processor.py --create-sample --video-dir $demoVideoDir --output-dir $demoOutputDir
```
