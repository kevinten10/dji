# Development Guide

This repository is a static DJI drone learning project with small browser demos
and a local Python video-processing workflow.

## Project Surfaces

- `index.html` is the static landing page.
- `simulation-simulator/` contains the Three.js drone simulator.
- `games/drone-game/` contains the Canvas obstacle game.
- `docs/` contains learning material and safety guidance.
- `ai_video_processor.py` processes local drone video files with FFmpeg and AI
  vision backends.

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

## Run The AI Video Processor

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install FFmpeg, then choose an AI backend:

```bash
# Default: local Ollama with LLaVA
ollama pull llava
set DJI_AI_BACKEND=ollama

# Optional cloud backends
set DJI_AI_BACKEND=zhipuai
set ZHIPUAI_API_KEY=your_key

set DJI_AI_BACKEND=openai
set OPENAI_API_KEY=your_key

set DJI_AI_BACKEND=anthropic
set ANTHROPIC_API_KEY=your_key
```

Run:

```bash
python ai_video_processor.py
```

Useful environment overrides:

```bash
set DJI_VIDEO_DIR=videos
set DJI_OUTPUT_DIR=output
set DJI_NUM_FRAMES=6
set DJI_CLIP_DURATION=5
set DJI_OLLAMA_MODEL=llava
```

`videos/` and `output/` are intentionally ignored by Git because they are local
source media and generated artifacts.

## Verification Checklist

Before publishing changes:

```bash
python -m py_compile ai_video_processor.py examples/python/drone_control.py
python -m http.server 8000
```

Then smoke-test the three browser routes listed above. The expected result is
that the home page renders, both demo links open, and the simulator/game primary
controls respond without console errors.

## Deployment

The project can be deployed as static files. `vercel.json` enables clean URLs
and disables trailing slashes. No build step is required.
