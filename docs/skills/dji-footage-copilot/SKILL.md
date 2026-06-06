---
name: dji-footage-copilot
description: Use when turning DJI drone footage into structured local analysis, edit notes, clips, telemetry summaries, and publish copy.
---

# DJI Footage Copilot Skill

Use this skill when a user has DJI aerial footage and wants a local, privacy-aware
processing workflow rather than a generic drone tutorial.

## Primary Goal

Turn local DJI videos and same-name `.SRT` telemetry files into:

- video metadata from FFprobe
- review frames from FFmpeg
- fixed clips and optional scene-based clips
- DJI SRT telemetry summaries
- AI frame analysis
- edit notes, title ideas, descriptions, tags, and publish recommendations
- `analysis.json` and `report.json`

## Default Workflow

1. Confirm local requirements: FFmpeg/FFprobe installed, Python dependencies installed.
2. Run the no-AI demo first:

   ```bash
   python ai_video_processor.py --create-sample
   ```

3. For real footage, place files like this:

   ```text
   videos/DJI_0001.MP4
   videos/DJI_0001.SRT
   ```

4. Run a private local analysis:

   ```bash
   python ai_video_processor.py --no-ai
   ```

5. Enable AI only after the user chooses a backend:

   ```bash
   ollama pull llava
   ollama serve
   python ai_video_processor.py --with-ai
   ```

## Safety Rules

- Do not commit `videos/`, `output/`, API keys, source footage, generated clips, or private GPS data.
- Prefer local Ollama for first-run demos.
- Treat DJI SRT telemetry as potentially sensitive location data.
- Use cloud AI backends only when the user explicitly configures the API key and understands the upload implications.

## Useful Commands

```bash
python ai_video_processor.py --create-sample
python ai_video_processor.py --no-ai --frames 4 --clip-duration 8
python ai_video_processor.py --scene-detect --no-ai
python -m py_compile ai_video_processor.py examples/python/drone_control.py
git diff --check
```

## Output Review Checklist

- `output/report.json` exists and includes `workflow_version`, `total_videos`, `results`.
- Each processed video has `analysis.json`.
- `video` includes duration, resolution, codec, size, and FPS when FFprobe can read them.
- `telemetry.exists` is true when a same-name SRT exists.
- `frames/` and `clips/` contain generated review assets when FFmpeg succeeds.
- `scene_detection.error` is informative when PySceneDetect is not installed.
