"""
DJI Footage Copilot
===================
Local AI workflow for DJI aerial footage.

The processor scans local DJI videos, reads video metadata with FFprobe,
extracts review frames with FFmpeg, optionally detects scenes with
PySceneDetect, parses same-name DJI SRT telemetry, and creates structured
analysis reports for editing and publishing.
"""

import base64
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

import requests
from tqdm import tqdm


WORKFLOW_VERSION = "3.0.0"
VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv")

CONFIG = {
    "ai_backend": "ollama",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llava",
    "zhipu_api_key": os.getenv("ZHIPUAI_API_KEY", ""),
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "openai_model": "gpt-4o",
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
    "anthropic_model": "claude-3-5-sonnet-20241022",
    "video_dir": "./videos",
    "output_dir": "./output",
    "num_frames": 6,
    "clip_duration": 5,
    "quality": 23,
    "enable_ai_analysis": True,
    "enable_auto_edit": True,
    "enable_scene_detection": False,
    "enable_scene_clips": False,
    "scene_threshold": 27.0,
}


def parse_bool(value):
    """Parse common environment-variable booleans."""
    if value is None or value == "":
        return None
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def apply_env_config():
    """Apply optional environment-variable overrides without editing source."""
    env_map = {
        "DJI_AI_BACKEND": "ai_backend",
        "DJI_OLLAMA_URL": "ollama_url",
        "DJI_OLLAMA_MODEL": "ollama_model",
        "DJI_VIDEO_DIR": "video_dir",
        "DJI_OUTPUT_DIR": "output_dir",
        "DJI_NUM_FRAMES": "num_frames",
        "DJI_CLIP_DURATION": "clip_duration",
        "DJI_QUALITY": "quality",
        "DJI_SCENE_THRESHOLD": "scene_threshold",
    }
    bool_env_map = {
        "DJI_ENABLE_AI_ANALYSIS": "enable_ai_analysis",
        "DJI_ENABLE_AUTO_EDIT": "enable_auto_edit",
        "DJI_ENABLE_SCENE_DETECTION": "enable_scene_detection",
        "DJI_ENABLE_SCENE_CLIPS": "enable_scene_clips",
    }

    int_keys = {"num_frames", "clip_duration", "quality"}
    float_keys = {"scene_threshold"}
    valid_backends = {"ollama", "zhipuai", "openai", "anthropic"}

    for env_name, config_key in env_map.items():
        value = os.getenv(env_name)
        if value is None or value == "":
            continue

        if config_key in int_keys:
            try:
                CONFIG[config_key] = int(value)
            except ValueError:
                print(f"[!] Ignoring invalid integer for {env_name}: {value}")
            continue

        if config_key in float_keys:
            try:
                CONFIG[config_key] = float(value)
            except ValueError:
                print(f"[!] Ignoring invalid number for {env_name}: {value}")
            continue

        if config_key == "ai_backend":
            value = value.lower()
            if value not in valid_backends:
                print(f"[!] Ignoring invalid backend {value}. Valid: {', '.join(sorted(valid_backends))}")
                continue

        CONFIG[config_key] = value

    for env_name, config_key in bool_env_map.items():
        value = parse_bool(os.getenv(env_name))
        if value is not None:
            CONFIG[config_key] = value


def run_cmd(args, description=""):
    """Execute a command and return True when it exits successfully."""
    if description:
        print(f"[*] {description}...")
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[!] Command failed: {' '.join(str(arg) for arg in args)}")
        if result.stderr:
            print(f"    Error: {result.stderr.strip()}")
        return False
    return True


def check_tool(name):
    """Return True if a command-line tool is available."""
    result = subprocess.run([name, "-version"], capture_output=True, text=True)
    return result.returncode == 0


def write_json(path, payload):
    """Write pretty UTF-8 JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def parse_fraction(value):
    """Parse FFprobe fraction strings such as 30000/1001."""
    if not value or value in {"0/0", "N/A"}:
        return None
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        try:
            denominator = float(denominator)
            if denominator == 0:
                return None
            return round(float(numerator) / denominator, 3)
        except ValueError:
            return None
    try:
        return round(float(value), 3)
    except ValueError:
        return None


def format_seconds(seconds):
    """Format seconds as a compact mm:ss label."""
    try:
        seconds = max(0, float(seconds))
    except (TypeError, ValueError):
        seconds = 0
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"
    return f"{minutes:02d}:{sec:02d}"


def scan_video_files(video_dir):
    """Find supported video files without touching local media contents."""
    video_dir = Path(video_dir)
    if not video_dir.exists():
        return []

    files = []
    for path in video_dir.iterdir():
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            files.append(path)
    return sorted(files)


def ffprobe_json(video_path):
    """Read video metadata with FFprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-show_entries",
            "format=duration,size,bit_rate,format_name",
            "-show_entries",
            "stream=index,codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,bit_rate,tags",
            "-of",
            "json",
            str(video_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None, result.stderr.strip() or "ffprobe failed"
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"Could not parse ffprobe output: {exc}"


def get_video_info(video_path):
    """Build normalized metadata for one video."""
    video_path = Path(video_path)
    info = {
        "name": video_path.stem,
        "path": str(video_path),
        "extension": video_path.suffix.lower(),
        "duration_seconds": 0.0,
        "duration_label": "00:00",
        "size": video_path.stat().st_size if video_path.exists() else 0,
        "size_mb": round((video_path.stat().st_size if video_path.exists() else 0) / (1024 * 1024), 2),
        "width": 0,
        "height": 0,
        "codec": "unknown",
        "fps": None,
        "bit_rate": None,
        "format_name": None,
    }

    data, error = ffprobe_json(video_path)
    if error:
        info["metadata_error"] = error
        return info

    format_info = data.get("format", {})
    try:
        info["duration_seconds"] = round(float(format_info.get("duration", 0) or 0), 3)
    except (TypeError, ValueError):
        info["duration_seconds"] = 0.0
    try:
        info["size"] = int(format_info.get("size") or info["size"])
    except (TypeError, ValueError):
        pass
    try:
        info["bit_rate"] = int(format_info.get("bit_rate") or 0) or None
    except (TypeError, ValueError):
        info["bit_rate"] = None

    info["size_mb"] = round(info["size"] / (1024 * 1024), 2)
    info["duration_label"] = format_seconds(info["duration_seconds"])
    info["format_name"] = format_info.get("format_name")

    for stream in data.get("streams", []):
        if stream.get("codec_type") != "video":
            continue
        info["width"] = int(stream.get("width") or 0)
        info["height"] = int(stream.get("height") or 0)
        info["codec"] = stream.get("codec_name", "unknown")
        info["fps"] = parse_fraction(stream.get("avg_frame_rate")) or parse_fraction(stream.get("r_frame_rate"))
        try:
            info["video_bit_rate"] = int(stream.get("bit_rate") or 0) or None
        except (TypeError, ValueError):
            info["video_bit_rate"] = None
        break

    return info


def extract_frames(video_path, output_dir, video_info, num_frames=6, prefix="frame"):
    """Extract evenly spaced frames from a video."""
    print(f"\n[*] Extracting review frames from: {video_path}")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    duration = float(video_info.get("duration_seconds") or 0)
    if duration <= 0 or num_frames <= 0:
        return []

    frame_records = []
    for index in range(num_frames):
        timestamp = (duration / (num_frames + 1)) * (index + 1)
        output_path = output_dir / f"{prefix}_{index + 1:03d}.jpg"
        ok = run_cmd(
            [
                "ffmpeg",
                "-ss",
                f"{timestamp:.3f}",
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                "-y",
                str(output_path),
            ],
            f"Extracting frame {index + 1}/{num_frames} at {timestamp:.1f}s",
        )
        if ok:
            frame_records.append(
                {
                    "index": index + 1,
                    "timestamp_seconds": round(timestamp, 3),
                    "timestamp_label": format_seconds(timestamp),
                    "path": str(output_path),
                    "source": "uniform",
                }
            )
    return frame_records


def split_video(video_path, output_dir, video_info, clip_duration=5, scenes=None):
    """Split video into fixed-duration clips and optionally scene clips."""
    print(f"\n[*] Creating edit clips for: {video_path}")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    duration = float(video_info.get("duration_seconds") or 0)
    if duration <= 0:
        return []

    clip_records = []
    start_time = 0.0
    clip_index = 0
    while start_time < duration:
        end_time = min(start_time + clip_duration, duration)
        output_path = output_dir / f"clip_{clip_index:03d}.mp4"
        ok = run_cmd(
            [
                "ffmpeg",
                "-ss",
                f"{start_time:.3f}",
                "-i",
                str(video_path),
                "-t",
                f"{end_time - start_time:.3f}",
                "-c",
                "copy",
                "-y",
                str(output_path),
            ],
            f"Creating clip {clip_index}: {start_time:.1f}s - {end_time:.1f}s",
        )
        if ok:
            clip_records.append(
                {
                    "index": clip_index,
                    "source": "fixed_interval",
                    "start_seconds": round(start_time, 3),
                    "end_seconds": round(end_time, 3),
                    "duration_seconds": round(end_time - start_time, 3),
                    "path": str(output_path),
                }
            )
        start_time = end_time
        clip_index += 1

    if CONFIG["enable_scene_clips"] and scenes:
        scene_dir = output_dir / "scenes"
        scene_dir.mkdir(parents=True, exist_ok=True)
        for scene in scenes:
            output_path = scene_dir / f"scene_{scene['index']:03d}.mp4"
            ok = run_cmd(
                [
                    "ffmpeg",
                    "-ss",
                    f"{scene['start_seconds']:.3f}",
                    "-i",
                    str(video_path),
                    "-t",
                    f"{scene['duration_seconds']:.3f}",
                    "-c",
                    "copy",
                    "-y",
                    str(output_path),
                ],
                f"Creating scene clip {scene['index']}",
            )
            if ok:
                clip_records.append({**scene, "source": "scene_detection", "path": str(output_path)})

    return clip_records


def detect_scenes(video_path, output_dir):
    """Run optional PySceneDetect scene detection."""
    result = {
        "enabled": CONFIG["enable_scene_detection"],
        "available": False,
        "threshold": CONFIG["scene_threshold"],
        "scenes": [],
        "error": None,
        "output": None,
    }
    if not CONFIG["enable_scene_detection"]:
        result["error"] = "Scene detection disabled. Set DJI_ENABLE_SCENE_DETECTION=1 to enable."
        return result

    try:
        from scenedetect import SceneManager, open_video
        from scenedetect.detectors import ContentDetector
    except ImportError:
        result["error"] = "PySceneDetect is not installed. Install scenedetect[opencv] to enable scene detection."
        return result

    result["available"] = True
    try:
        video = open_video(str(video_path))
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=CONFIG["scene_threshold"]))
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()
        for index, (start, end) in enumerate(scene_list, start=1):
            start_seconds = round(start.get_seconds(), 3)
            end_seconds = round(end.get_seconds(), 3)
            result["scenes"].append(
                {
                    "index": index,
                    "start_seconds": start_seconds,
                    "end_seconds": end_seconds,
                    "duration_seconds": round(end_seconds - start_seconds, 3),
                    "start_timecode": start.get_timecode(),
                    "end_timecode": end.get_timecode(),
                }
            )
        output_path = Path(output_dir) / "scenes.json"
        write_json(output_path, result)
        result["output"] = str(output_path)
    except Exception as exc:
        result["error"] = f"Scene detection failed: {exc}"
    return result


def find_sidecar_srt(video_path):
    """Find DJI same-name SRT telemetry next to the video."""
    video_path = Path(video_path)
    candidates = [
        video_path.with_suffix(".SRT"),
        video_path.with_suffix(".srt"),
        video_path.with_suffix(".Srt"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def clean_srt_text(text):
    """Remove simple HTML tags and normalize whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


def extract_number(text, patterns):
    """Extract the first numeric value matching a list of regex patterns."""
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        try:
            return float(match.group(1))
        except (TypeError, ValueError):
            continue
    return None


def extract_text_value(text, patterns):
    """Extract the first text value matching a list of regex patterns."""
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


DJI_SRT_FIELD_PATTERNS = {
    "latitude": [r"(?:latitude|lat)\s*[:=]\s*(-?\d+(?:\.\d+)?)"],
    "longitude": [r"(?:longitude|lon|lng)\s*[:=]\s*(-?\d+(?:\.\d+)?)"],
    "relative_altitude": [r"(?:rel_alt|relative_alt|relative_altitude)\s*[:=]\s*(-?\d+(?:\.\d+)?)"],
    "absolute_altitude": [r"(?:abs_alt|absolute_alt|absolute_altitude)\s*[:=]\s*(-?\d+(?:\.\d+)?)"],
    "altitude": [r"(?:\baltitude|(?<!rel_)(?<!abs_)\balt)\s*[:=]\s*(-?\d+(?:\.\d+)?)"],
    "speed": [r"(?:speed|h_speed|horizontal_speed|vel_h)\s*[:=]\s*(-?\d+(?:\.\d+)?)"],
    "gimbal_pitch": [r"(?:gb_pitch|gimbal_pitch)\s*[:=]\s*(-?\d+(?:\.\d+)?)"],
    "gimbal_yaw": [r"(?:gb_yaw|gimbal_yaw)\s*[:=]\s*(-?\d+(?:\.\d+)?)"],
    "gimbal_roll": [r"(?:gb_roll|gimbal_roll)\s*[:=]\s*(-?\d+(?:\.\d+)?)"],
    "iso": [r"iso\s*[:=]\s*(\d+(?:\.\d+)?)"],
    "f_number": [r"(?:fnum|f_number|f-number)\s*[:=]\s*(\d+(?:\.\d+)?)"],
    "ev": [r"\bev\s*[:=]\s*(-?\d+(?:\.\d+)?)"],
    "color_temperature": [r"(?:ct|color_temp|color_temperature)\s*[:=]\s*(\d+(?:\.\d+)?)"],
    "focal_length": [r"(?:focal_len|focal_length)\s*[:=]\s*(\d+(?:\.\d+)?)"],
}


def parse_dji_srt(srt_path, max_samples=12):
    """Parse DJI telemetry from a same-name SRT sidecar file."""
    srt_path = Path(srt_path)
    telemetry = {
        "path": str(srt_path),
        "exists": srt_path.exists(),
        "cue_count": 0,
        "fields_detected": [],
        "samples": [],
        "stats": {},
        "parser_note": "Best-effort parser for common DJI SRT telemetry variants.",
    }
    if not srt_path.exists():
        return telemetry

    content = srt_path.read_text(encoding="utf-8-sig", errors="replace")
    blocks = re.split(r"\n\s*\n", content.strip())
    values_by_field = {field: [] for field in DJI_SRT_FIELD_PATTERNS}
    detected = set()

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue
        time_line = next((line for line in lines if "-->" in line), None)
        if not time_line:
            continue

        cue_text = clean_srt_text(" ".join(line for line in lines if "-->" not in line and not line.isdigit()))
        fields = {}
        for field, patterns in DJI_SRT_FIELD_PATTERNS.items():
            value = extract_number(cue_text, patterns)
            if value is not None:
                fields[field] = value
                values_by_field[field].append(value)
                detected.add(field)

        shutter = extract_text_value(cue_text, [r"shutter\s*[:=]\s*([^\]\s]+)"])
        if shutter:
            fields["shutter"] = shutter
            detected.add("shutter")

        telemetry["cue_count"] += 1
        if len(telemetry["samples"]) < max_samples:
            telemetry["samples"].append(
                {
                    "index": telemetry["cue_count"],
                    "timecode": time_line,
                    "text": cue_text[:500],
                    "fields": fields,
                }
            )

    telemetry["fields_detected"] = sorted(detected)
    for field, values in values_by_field.items():
        if values:
            telemetry["stats"][field] = {
                "min": round(min(values), 6),
                "max": round(max(values), 6),
                "first": round(values[0], 6),
                "last": round(values[-1], 6),
            }
    return telemetry


def build_publish_recommendations(video_info, telemetry, scene_detection, clips):
    """Create practical editing and publishing suggestions from available metadata."""
    width = video_info.get("width") or 0
    height = video_info.get("height") or 0
    duration = video_info.get("duration_seconds") or 0
    aspect = "unknown"
    if width and height:
        if width > height:
            aspect = "landscape"
        elif height > width:
            aspect = "vertical"
        else:
            aspect = "square"

    formats = []
    if aspect == "landscape":
        formats.extend(["YouTube/Bilibili 16:9", "website hero background", "client presentation B-roll"])
    elif aspect == "vertical":
        formats.extend(["Douyin/Reels/Shorts 9:16", "travel vlog short clip"])
    else:
        formats.extend(["square social feed", "thumbnail source"])

    edit_notes = [
        "Review the extracted frames before AI analysis to remove takeoff/landing-only footage.",
        "Use fixed clips for quick review; enable PySceneDetect when the source contains multiple camera moves.",
    ]
    if telemetry.get("exists"):
        edit_notes.append("Use SRT telemetry to identify altitude, GPS, camera, and gimbal changes before choosing highlight moments.")
    else:
        edit_notes.append("No same-name SRT was found; keep telemetry-aware recommendations disabled for this file.")
    if scene_detection.get("scenes"):
        edit_notes.append("Scene list is available; use scene boundaries as first-pass cut points.")

    recommended_clip_count = min(len(clips), 12)
    return {
        "recommended_formats": formats,
        "recommended_clip_count": recommended_clip_count,
        "duration_bucket": "short" if duration < 60 else "medium" if duration < 300 else "long",
        "editing_notes": edit_notes,
        "publish_copy_brief": {
            "title_direction": "地点 + 航拍视角 + 情绪关键词",
            "description_direction": "交代地点、天气/光线、飞行视角和最值得看的镜头。",
            "tag_groups": ["DJI", "航拍", "无人机", "旅行", "风光"],
        },
    }


def encode_image_to_base64(image_path):
    """Encode image to base64 string."""
    with open(image_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


def call_ollama_vision(image_path, prompt):
    """Call Ollama with LLaVA for local vision analysis."""
    print("[*] Using Ollama (local) for vision analysis...")
    try:
        response = requests.get(f"{CONFIG['ollama_url']}/api/tags", timeout=10)
        if response.status_code != 200:
            return None, "Ollama is not running. Please start Ollama first."
    except Exception:
        return None, "Cannot connect to Ollama. Please make sure Ollama is installed and running."

    payload = {
        "model": CONFIG["ollama_model"],
        "prompt": prompt,
        "images": [encode_image_to_base64(image_path)],
        "stream": False,
    }

    try:
        response = requests.post(f"{CONFIG['ollama_url']}/api/generate", json=payload, timeout=120)
        if response.status_code == 200:
            return response.json().get("response", ""), None
        return None, f"Ollama error: {response.status_code} - {response.text}"
    except Exception as exc:
        return None, f"Ollama request failed: {exc}"


def call_zhipu_vision(image_path, prompt):
    """Call ZhipuAI GLM-4V for vision analysis."""
    if not CONFIG["zhipu_api_key"]:
        return None, "ZHIPUAI_API_KEY not set"

    from zhipuai import ZhipuAI

    client = ZhipuAI(api_key=CONFIG["zhipu_api_key"])
    try:
        response = client.chat.completions.create(
            model="glm-4v",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image_to_base64(image_path)}"}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        return response.choices[0].message.content, None
    except Exception as exc:
        return None, f"ZhipuAI error: {exc}"


def call_openai_vision(image_path, prompt):
    """Call OpenAI GPT-4o for vision analysis."""
    if not CONFIG["openai_api_key"]:
        return None, "OPENAI_API_KEY not set"

    payload = {
        "model": CONFIG["openai_model"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image_to_base64(image_path)}"}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "max_tokens": 1000,
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {CONFIG['openai_api_key']}", "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None
        return None, f"OpenAI error: {response.status_code} - {response.text}"
    except Exception as exc:
        return None, f"OpenAI request failed: {exc}"


def call_anthropic_vision(image_path, prompt):
    """Call Anthropic Claude for vision analysis."""
    if not CONFIG["anthropic_api_key"]:
        return None, "ANTHROPIC_API_KEY not set"

    payload = {
        "model": CONFIG["anthropic_model"],
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": encode_image_to_base64(image_path),
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": CONFIG["anthropic_api_key"],
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120,
        )
        if response.status_code == 200:
            return response.json()["content"][0]["text"], None
        return None, f"Anthropic error: {response.status_code} - {response.text}"
    except Exception as exc:
        return None, f"Anthropic request failed: {exc}"


def analyze_frame_with_ai(frame_record, frame_number, total_frames, video_info, telemetry):
    """Analyze a single extracted frame using the configured AI backend."""
    telemetry_hint = "SRT telemetry is available." if telemetry.get("exists") else "No DJI SRT telemetry was found."
    prompt = f"""You are a professional drone footage editor.

Analyze frame {frame_number} of {total_frames} from DJI aerial footage.

Video metadata:
- duration: {video_info.get('duration_label')}
- resolution: {video_info.get('width')}x{video_info.get('height')}
- codec: {video_info.get('codec')}
- telemetry: {telemetry_hint}

Return concise practical notes:
1. Scene/subject/environment
2. Camera angle and motion impression
3. Lighting and color mood
4. Whether this frame suggests a highlight, transition, B-roll, establishing shot, or discard
5. Editing recommendation in one sentence
"""

    backend = CONFIG["ai_backend"]
    image_path = frame_record["path"]
    if backend == "ollama":
        return call_ollama_vision(image_path, prompt)
    if backend == "zhipuai":
        return call_zhipu_vision(image_path, prompt)
    if backend == "openai":
        return call_openai_vision(image_path, prompt)
    if backend == "anthropic":
        return call_anthropic_vision(image_path, prompt)
    return None, f"Unknown AI backend: {backend}"


def generate_video_script(frame_analyses, video_name, telemetry, publish_package):
    """Generate a publishing package based on frame analyses."""
    telemetry_context = (
        f"Telemetry fields detected: {', '.join(telemetry.get('fields_detected', []))}"
        if telemetry.get("fields_detected")
        else "No telemetry fields detected."
    )
    prompt = f"""You are a Chinese short-video editor for DJI aerial footage.

Create a compact publish package for the video "{video_name}".

Context:
- {telemetry_context}
- Recommended formats: {', '.join(publish_package.get('recommended_formats', []))}

Frame analyses:
{frame_analyses}

Return JSON with:
{{
  "title": "Chinese title",
  "description": "Chinese description, 80-120 Chinese characters",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "music_mood": "music mood",
  "cutting_plan": ["shot 1", "shot 2", "shot 3"]
}}"""

    backend = CONFIG["ai_backend"]
    if backend == "ollama":
        try:
            response = requests.post(
                f"{CONFIG['ollama_url']}/api/generate",
                json={"model": CONFIG["ollama_model"], "prompt": prompt, "stream": False},
                timeout=120,
            )
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as exc:
            print(f"    [!] Ollama script generation error: {exc}")
        return "Could not generate publish copy with Ollama."

    if backend == "zhipuai" and CONFIG["zhipu_api_key"]:
        from zhipuai import ZhipuAI

        client = ZhipuAI(api_key=CONFIG["zhipu_api_key"])
        try:
            response = client.chat.completions.create(model="glm-4", messages=[{"role": "user", "content": prompt}])
            return response.choices[0].message.content
        except Exception as exc:
            return f"ZhipuAI script generation failed: {exc}"

    if backend == "openai" and CONFIG["openai_api_key"]:
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {CONFIG['openai_api_key']}"},
                json={"model": CONFIG["openai_model"], "messages": [{"role": "user", "content": prompt}]},
                timeout=120,
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            return f"OpenAI script generation failed: {exc}"

    if backend == "anthropic" and CONFIG["anthropic_api_key"]:
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": CONFIG["anthropic_api_key"], "anthropic-version": "2023-06-01"},
                json={
                    "model": CONFIG["anthropic_model"],
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=120,
            )
            if response.status_code == 200:
                return response.json()["content"][0]["text"]
        except Exception as exc:
            return f"Anthropic script generation failed: {exc}"

    return "Publish copy generation skipped because no valid AI backend is configured."


def process_video(video_path):
    """Process a single video file into analysis, clips, telemetry, and report data."""
    print(f"\n{'=' * 70}")
    print(f"PROCESSING: {video_path}")
    print(f"{'=' * 70}")

    video_path = Path(video_path)
    video_name = video_path.stem
    video_output_dir = Path(CONFIG["output_dir"]) / video_name
    frames_output_dir = video_output_dir / "frames"
    clips_output_dir = video_output_dir / "clips"
    video_output_dir.mkdir(parents=True, exist_ok=True)

    video_info = get_video_info(video_path)
    print(f"    Duration: {video_info.get('duration_label')}")
    print(f"    Resolution: {video_info.get('width', 0)}x{video_info.get('height', 0)}")
    print(f"    FPS: {video_info.get('fps') or 'unknown'}")
    print(f"    Size: {video_info.get('size_mb', 0)} MB")

    srt_path = find_sidecar_srt(video_path)
    telemetry = parse_dji_srt(srt_path) if srt_path else {
        "path": None,
        "exists": False,
        "cue_count": 0,
        "fields_detected": [],
        "samples": [],
        "stats": {},
        "parser_note": "No same-name DJI SRT sidecar found.",
    }
    if telemetry["exists"]:
        print(f"    SRT telemetry: {telemetry['cue_count']} cues, fields: {', '.join(telemetry['fields_detected']) or 'none'}")
    else:
        print("    SRT telemetry: not found")

    scene_detection = detect_scenes(video_path, video_output_dir)
    if scene_detection["enabled"]:
        if scene_detection["scenes"]:
            print(f"    Scenes detected: {len(scene_detection['scenes'])}")
        else:
            print(f"    Scenes detected: 0 ({scene_detection.get('error') or 'no cuts found'})")

    frame_records = extract_frames(video_path, frames_output_dir, video_info, CONFIG["num_frames"])
    print(f"    Extracted frames: {len(frame_records)}")

    clip_records = []
    if CONFIG["enable_auto_edit"]:
        clip_records = split_video(
            video_path,
            clips_output_dir,
            video_info,
            CONFIG["clip_duration"],
            scene_detection.get("scenes"),
        )
        print(f"    Created clips: {len(clip_records)}")

    publish_package = build_publish_recommendations(video_info, telemetry, scene_detection, clip_records)
    frame_analyses = []
    if CONFIG["enable_ai_analysis"] and frame_records:
        print(f"\n[*] Analyzing frames with AI ({CONFIG['ai_backend']})...")
        for index, frame_record in enumerate(tqdm(frame_records, desc="Analyzing")):
            analysis, error = analyze_frame_with_ai(frame_record, index + 1, len(frame_records), video_info, telemetry)
            if analysis:
                frame_analyses.append({**frame_record, "analysis": analysis})
                print(f"    Frame {index + 1}: analyzed")
            else:
                frame_analyses.append({**frame_record, "analysis": None, "error": error})
                print(f"    Frame {index + 1}: skipped - {error}")

    generated_script = None
    successful_analyses = [item for item in frame_analyses if item.get("analysis")]
    if successful_analyses:
        print("\n[*] Generating publish copy...")
        analyses_text = "\n".join(
            f"{item['timestamp_label']} frame {item['index']}: {item['analysis']}" for item in successful_analyses
        )
        generated_script = generate_video_script(analyses_text, video_name, telemetry, publish_package)
        print("    Publish copy generated")

    analysis = {
        "workflow_version": WORKFLOW_VERSION,
        "processed_at": datetime.now().isoformat(),
        "name": video_name,
        "video": video_info,
        "telemetry": telemetry,
        "scene_detection": scene_detection,
        "frames": frame_records,
        "clips": clip_records,
        "frame_analyses": frame_analyses,
        "publish_package": publish_package,
        "generated_script": generated_script,
    }

    analysis_path = video_output_dir / "analysis.json"
    write_json(analysis_path, analysis)
    print(f"\n[OK] Analysis saved to: {analysis_path}")
    return analysis


def build_empty_report(video_dir, reason):
    """Build a report for safe empty-input runs."""
    return {
        "workflow_version": WORKFLOW_VERSION,
        "processed_at": datetime.now().isoformat(),
        "input_dir": str(video_dir),
        "output_dir": str(CONFIG["output_dir"]),
        "ai_backend": CONFIG["ai_backend"],
        "total_videos": 0,
        "total_duration_seconds": 0,
        "status": "no_input",
        "reason": reason,
        "results": [],
    }


def main():
    """Main entry point."""
    apply_env_config()

    print(
        """
============================================================
 DJI Footage Copilot v3.0
 Local AI workflow for DJI aerial video processing
============================================================
"""
    )
    print(f"[*] Input directory: {CONFIG['video_dir']}")
    print(f"[*] Output directory: {CONFIG['output_dir']}")
    print(f"[*] AI backend: {CONFIG['ai_backend']}")

    output_dir = Path(CONFIG["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    video_dir = Path(CONFIG["video_dir"])
    if not video_dir.exists():
        print(f"[!] Video directory not found: {video_dir}")
        report = build_empty_report(video_dir, "video directory not found")
        write_json(output_dir / "report.json", report)
        print(f"[OK] Empty report saved to: {output_dir / 'report.json'}")
        return

    video_files = scan_video_files(video_dir)
    if not video_files:
        print(f"[!] No video files found in {video_dir}")
        report = build_empty_report(video_dir, "no supported video files found")
        write_json(output_dir / "report.json", report)
        print(f"[OK] Empty report saved to: {output_dir / 'report.json'}")
        return

    print("[*] Checking FFmpeg/FFprobe...")
    if not check_tool("ffmpeg") or not check_tool("ffprobe"):
        print("[!] FFmpeg or FFprobe not found. Please install FFmpeg first.")
        print("    Windows: winget install ffmpeg")
        print("    macOS: brew install ffmpeg")
        print("    Linux: sudo apt install ffmpeg")
        return

    if CONFIG["ai_backend"] == "ollama":
        print("[*] Ollama selected. Start it with: ollama serve")
    elif CONFIG["ai_backend"] == "zhipuai" and not CONFIG["zhipu_api_key"]:
        print("[!] ZhipuAI selected but ZHIPUAI_API_KEY is not set.")
        return
    elif CONFIG["ai_backend"] == "openai" and not CONFIG["openai_api_key"]:
        print("[!] OpenAI selected but OPENAI_API_KEY is not set.")
        return
    elif CONFIG["ai_backend"] == "anthropic" and not CONFIG["anthropic_api_key"]:
        print("[!] Anthropic selected but ANTHROPIC_API_KEY is not set.")
        return

    print(f"[*] Found {len(video_files)} video file(s)")

    results = []
    for video_path in video_files:
        try:
            results.append(process_video(video_path))
        except Exception as exc:
            print(f"[!] Error processing {video_path}: {exc}")
            results.append({"name": video_path.stem, "path": str(video_path), "error": str(exc)})

    total_duration = sum((item.get("video", {}) or {}).get("duration_seconds", 0) for item in results)
    report = {
        "workflow_version": WORKFLOW_VERSION,
        "processed_at": datetime.now().isoformat(),
        "input_dir": str(video_dir),
        "output_dir": str(output_dir),
        "ai_backend": CONFIG["ai_backend"],
        "total_videos": len(results),
        "total_duration_seconds": round(total_duration, 3),
        "outputs": {
            "report": str(output_dir / "report.json"),
            "per_video_analysis": str(output_dir / "<video_name>" / "analysis.json"),
            "frames": str(output_dir / "<video_name>" / "frames"),
            "clips": str(output_dir / "<video_name>" / "clips"),
            "scenes": str(output_dir / "<video_name>" / "scenes.json"),
        },
        "results": results,
    }
    write_json(output_dir / "report.json", report)

    print(f"\n{'=' * 70}")
    print("PROCESSING COMPLETE")
    print(f"{'=' * 70}")
    print(f"[OK] Summary report saved to: {output_dir / 'report.json'}")
    print(f"[OK] Individual analyses saved in: {output_dir / '<video_name>' / 'analysis.json'}")
    print("\n[*] Done!")


if __name__ == "__main__":
    main()
