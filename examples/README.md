# Examples

These files make the project easy to understand before you bring real DJI footage.

## Fastest Demo

Generate a tiny local MP4 plus a same-name DJI-style SRT, then process it without AI:

```bash
python ai_video_processor.py --create-sample
```

This writes local demo media to `videos/` and generated reports to `output/`.
Both folders are ignored by Git.

## Included Files

- `sample-dji-srt/DJI_SAMPLE.SRT`: a small DJI-style telemetry sidecar.
- `sample-output/report.example.json`: a compact example of the batch report shape.

The sample SRT is intentionally small and synthetic. Real DJI files may contain
more fields or slightly different names; the parser keeps raw samples for future
format expansion.
