"""
DJI AI Video Processor
=======================
AI-powered drone video analysis and editing tool

Supports multiple AI backends:
- Ollama (FREE, local) - RECOMMENDED
- ZhipuAI (GLM-4V)
- OpenAI (GPT-4o)
- Anthropic (Claude)

Quick Start:
1. For FREE local AI: Download Ollama from https://ollama.com
   Then run: ollama pull llava

2. Set environment variable for your AI backend:
   - Ollama: No API key needed (runs locally)
   - ZhipuAI: set ZHIPUAI_API_KEY
   - OpenAI: set OPENAI_API_KEY
   - Claude: set ANTHROPIC_API_KEY

3. Run: python ai_video_processor.py
"""

import os
import sys
import json
import subprocess
import base64
import requests
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    # AI Backend selection
    # Options: "ollama", "zhipuai", "openai", "anthropic"
    "ai_backend": "ollama",

    # Ollama settings (FREE, local)
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llava",

    # ZhipuAI settings
    "zhipu_api_key": os.getenv("ZHIPUAI_API_KEY", ""),

    # OpenAI settings
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "openai_model": "gpt-4o",

    # Anthropic settings
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
    "anthropic_model": "claude-3-5-sonnet-20241022",

    # Paths
    "video_dir": "./videos",
    "output_dir": "./output",

    # Processing options
    "num_frames": 6,
    "clip_duration": 5,
    "quality": 23,
    "enable_ai_analysis": True,
    "enable_auto_edit": True,
}


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
    }

    int_keys = {"num_frames", "clip_duration", "quality"}
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

        if config_key == "ai_backend":
            value = value.lower()
            if value not in valid_backends:
                print(f"[!] Ignoring invalid backend {value}. Valid: {', '.join(sorted(valid_backends))}")
                continue

        CONFIG[config_key] = value

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def run_cmd(cmd, description=""):
    """Execute system command"""
    if description:
        print(f"[*] {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[!] Command failed: {cmd}")
        print(f"    Error: {result.stderr}")
        return False
    return True


def extract_frames(video_path, output_dir, num_frames=6):
    """Extract frames from video at evenly spaced intervals"""
    print(f"\n[*] Extracting frames from: {video_path}")

    os.makedirs(output_dir, exist_ok=True)

    # Get video duration
    cmd = f'ffprobe -v quiet -show_entries format=duration -of json "{video_path}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    duration = 30  # default fallback

    try:
        data = json.loads(result.stdout)
        duration = float(data['format']['duration'])
    except:
        pass

    # Extract frames
    frame_paths = []
    for i in range(num_frames):
        timestamp = (duration / (num_frames + 1)) * (i + 1)
        output_path = os.path.join(output_dir, f"frame_{i+1:03d}.jpg")

        cmd = f'ffmpeg -ss {timestamp} -i "{video_path}" -frames:v 1 -y "{output_path}"'
        if run_cmd(cmd, f"Extracting frame {i+1}/{num_frames} at {timestamp:.1f}s"):
            frame_paths.append(output_path)

    return frame_paths


def split_video(video_path, output_dir, clip_duration=5):
    """Split video into clips of specified duration"""
    print(f"\n[*] Splitting video: {video_path}")

    os.makedirs(output_dir, exist_ok=True)

    # Get video duration
    cmd = f'ffprobe -v quiet -show_entries format=duration -of json "{video_path}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    try:
        data = json.loads(result.stdout)
        duration = float(data['format']['duration'])
    except:
        duration = 30

    # Split into clips
    clip_paths = []
    start_time = 0
    clip_index = 0

    while start_time < duration:
        end_time = min(start_time + clip_duration, duration)
        output_path = os.path.join(output_dir, f"clip_{clip_index:03d}.mp4")

        cmd = f'ffmpeg -ss {start_time} -i "{video_path}" -t {end_time - start_time} -c copy -y "{output_path}"'
        if run_cmd(cmd, f"Creating clip {clip_index}: {start_time:.1f}s - {end_time:.1f}s"):
            clip_paths.append(output_path)

        start_time = end_time
        clip_index += 1

    return clip_paths


def encode_image_to_base64(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ============================================================================
# AI BACKENDS
# ============================================================================

def call_ollama_vision(image_path, prompt):
    """
    Call Ollama with LLaVA for free local vision analysis
    Download Ollama from https://ollama.com
    Then run: ollama pull llava
    """
    print(f"[*] Using Ollama (free, local) for vision analysis...")

    # Check if Ollama is running
    try:
        response = requests.get(f"{CONFIG['ollama_url']}/api/tags")
        if response.status_code != 200:
            return None, "Ollama is not running. Please start Ollama first."
    except:
        return None, "Cannot connect to Ollama. Please make sure Ollama is installed and running."

    # Encode image
    with open(image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    # Prepare request
    payload = {
        "model": CONFIG["ollama_model"],
        "prompt": prompt,
        "images": [img_base64],
        "stream": False
    }

    try:
        response = requests.post(
            f"{CONFIG['ollama_url']}/api/generate",
            json=payload,
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("response", ""), None
        else:
            return None, f"Ollama error: {response.status_code} - {response.text}"
    except Exception as e:
        return None, f"Ollama request failed: {str(e)}"


def call_zhipu_vision(image_path, prompt):
    """Call ZhipuAI GLM-4V for vision analysis"""
    if not CONFIG["zhipu_api_key"]:
        return None, "ZHIPUAI_API_KEY not set"

    from zhipuai import ZhipuAI
    client = ZhipuAI(api_key=CONFIG["zhipu_api_key"])

    with open(image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    try:
        response = client.chat.completions.create(
            model="glm-4v",
            messages=[{
                "role": "user",
                "content": [{
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                }, {
                    "type": "text",
                    "text": prompt
                }]
            }]
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, f"ZhipuAI error: {str(e)}"


def call_openai_vision(image_path, prompt):
    """Call OpenAI GPT-4o for vision analysis"""
    if not CONFIG["openai_api_key"]:
        return None, "OPENAI_API_KEY not set"

    with open(image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {CONFIG['openai_api_key']}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": CONFIG["openai_model"],
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }],
        "max_tokens": 1000
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"], None
        else:
            return None, f"OpenAI error: {response.status_code} - {response.text}"
    except Exception as e:
        return None, f"OpenAI request failed: {str(e)}"


def call_anthropic_vision(image_path, prompt):
    """Call Anthropic Claude for vision analysis"""
    if not CONFIG["anthropic_api_key"]:
        return None, "ANTHROPIC_API_KEY not set"

    with open(image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    headers = {
        "x-api-key": CONFIG["anthropic_api_key"],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }

    payload = {
        "model": CONFIG["anthropic_model"],
        "max_tokens": 1024,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": img_base64
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }]
    }

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            return result["content"][0]["text"], None
        else:
            return None, f"Anthropic error: {response.status_code} - {response.text}"
    except Exception as e:
        return None, f"Anthropic request failed: {str(e)}"


def analyze_frame_with_ai(image_path, frame_number, total_frames):
    """Analyze a single frame using the configured AI backend"""

    prompt = f"""You are an expert drone aerial photographer and video editor.

Analyze this drone footage frame {frame_number} of {total_frames}.

Please provide a brief analysis covering:
1. What is shown in this frame (scene, subject, environment)
2. The shooting angle and perspective (low altitude, high altitude, oblique, etc.)
3. Lighting conditions and time of day
4. Color tone and visual style
5. Key highlights or interesting elements
6. Suggested use cases for this footage (B-roll, main shot, cutaway, etc.)

Be concise and practical. Your analysis will be used to create an engaging video."""

    backend = CONFIG["ai_backend"]

    if backend == "ollama":
        return call_ollama_vision(image_path, prompt)
    elif backend == "zhipuai":
        return call_zhipu_vision(image_path, prompt)
    elif backend == "openai":
        return call_openai_vision(image_path, prompt)
    elif backend == "anthropic":
        return call_anthropic_vision(image_path, prompt)
    else:
        return None, f"Unknown AI backend: {backend}"


def generate_video_script(frame_analyses, video_name):
    """Generate a video script based on frame analyses"""

    prompt = f"""You are a professional video script writer for drone aerial footage.

Based on the following AI analysis of drone video frames, create:
1. A catchy video title (in Chinese)
2. A compelling description/script (in Chinese, about 100 words)
3. 5 relevant tags/labels
4. Suggested music mood

The footage appears to be from Yunnan, China (大理/丽江 area).

Frame analyses:
{frame_analyses}

Please provide your response in this JSON format:
{{
    "title": "Your video title in Chinese",
    "description": "Your video description/script in Chinese, about 100 words",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
    "music_mood": "Suggested music mood (e.g., epic, calm, exciting)"
}}"""

    backend = CONFIG["ai_backend"]

    # Use text-only AI for script generation
    if backend == "ollama":
        # FIX: Use llava model (already installed) instead of llama3.2
        try:
            response = requests.post(
                f"{CONFIG['ollama_url']}/api/generate",
                json={"model": CONFIG["ollama_model"], "prompt": prompt, "stream": False},
                timeout=120
            )
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            print(f"    [!] Ollama script generation error: {e}")
        return "Could not generate script with Ollama (is llava model installed?)"

    elif backend == "zhipuai" and CONFIG["zhipu_api_key"]:
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=CONFIG["zhipu_api_key"])
        try:
            response = client.chat.completions.create(
                model="glm-4",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except:
            pass

    elif backend == "openai" and CONFIG["openai_api_key"]:
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {CONFIG['openai_api_key']}"},
                json={"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}]},
                timeout=120
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
        except:
            pass

    elif backend == "anthropic" and CONFIG["anthropic_api_key"]:
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": CONFIG["anthropic_api_key"], "anthropic-version": "2023-06-01"},
                json={"model": CONFIG["anthropic_model"], "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]},
                timeout=120
            )
            if response.status_code == 200:
                return response.json()["content"][0]["text"]
        except:
            pass

    return "Script generation skipped (no valid API configured)"


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_video(video_path):
    """Process a single video file"""
    print(f"\n{'='*60}")
    print(f"PROCESSING: {video_path}")
    print(f"{'='*60}")

    video_name = Path(video_path).stem
    video_output_dir = os.path.join(CONFIG["output_dir"], video_name)
    frames_output_dir = os.path.join(video_output_dir, "frames")
    clips_output_dir = os.path.join(video_output_dir, "clips")

    os.makedirs(video_output_dir, exist_ok=True)

    # Extract video info - FIX: convert Path to str for JSON serialization
    print(f"\n[*] Getting video information...")
    cmd = f'ffprobe -v quiet -show_entries format=duration,size -show_entries stream=codec_name,width,height,tags -of json "{video_path}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    # FIX: Use str() to ensure path is serializable
    video_info = {"name": video_name, "path": str(video_path)}
    try:
        data = json.loads(result.stdout)
        format_info = data.get("format", {})
        video_info["duration"] = float(format_info.get("duration", 0))
        video_info["size"] = int(format_info.get("size", 0))
        video_info["size_mb"] = video_info["size"] / (1024 * 1024)

        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_info["width"] = stream.get("width", 0)
                video_info["height"] = stream.get("height", 0)
                video_info["codec"] = stream.get("codec_name", "unknown")
    except:
        pass

    print(f"    Duration: {video_info.get('duration', 0):.1f}s")
    print(f"    Resolution: {video_info.get('width', 0)}x{video_info.get('height', 0)}")
    print(f"    Size: {video_info.get('size_mb', 0):.1f} MB")

    # Extract frames
    frame_paths = extract_frames(video_path, frames_output_dir, CONFIG["num_frames"])
    video_info["frame_count"] = len(frame_paths)
    print(f"    Extracted frames: {len(frame_paths)}")

    # Split into clips
    if CONFIG["enable_auto_edit"]:
        clip_paths = split_video(video_path, clips_output_dir, CONFIG["clip_duration"])
        video_info["clip_count"] = len(clip_paths)
        print(f"    Created clips: {len(clip_paths)}")

    # AI Analysis
    if CONFIG["enable_ai_analysis"] and frame_paths:
        print(f"\n[*] Analyzing frames with AI ({CONFIG['ai_backend']})...")

        frame_analyses = []
        for i, frame_path in enumerate(tqdm(frame_paths, desc="Analyzing")):
            analysis, error = analyze_frame_with_ai(frame_path, i + 1, len(frame_paths))

            if analysis:
                # FIX: Ensure path is string for JSON serialization
                frame_analyses.append({
                    "frame": i + 1,
                    "path": str(frame_path),
                    "analysis": analysis
                })
                print(f"    Frame {i+1}: Analyzed successfully")
            else:
                print(f"    Frame {i+1}: Failed - {error}")

        video_info["frame_analyses"] = frame_analyses

        # Generate script
        if frame_analyses:
            print(f"\n[*] Generating video script...")
            analyses_text = "\n".join([f"Frame {a['frame']}: {a['analysis']}" for a in frame_analyses])
            script = generate_video_script(analyses_text, video_name)
            video_info["generated_script"] = script
            print(f"    Script generated")

    # Save analysis
    analysis_path = os.path.join(video_output_dir, "analysis.json")
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(video_info, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Analysis saved to: {analysis_path}")

    return video_info


def main():
    """Main entry point"""
    apply_env_config()

    print("""
============================================================
 DJI AI Video Processor v2.0
 AI-powered drone video analysis & editing
============================================================
    """)

    # Check FFmpeg
    print("[*] Checking FFmpeg...")
    result = subprocess.run("ffmpeg -version", shell=True, capture_output=True)
    if result.returncode != 0:
        print("[!] FFmpeg not found. Please install FFmpeg first.")
        print("    Windows: winget install ffmpeg")
        print("    Mac: brew install ffmpeg")
        print("    Linux: sudo apt install ffmpeg")
        return

    # Check AI backend
    print(f"[*] Using AI backend: {CONFIG['ai_backend']}")

    if CONFIG["ai_backend"] == "ollama":
        print("[*] Ollama (free, local) - No API key needed!")
        print("[*] Make sure Ollama is running: ollama serve")
        print("[*] If not installed: Download from https://ollama.com")
    elif CONFIG["ai_backend"] == "zhipuai":
        if not CONFIG["zhipu_api_key"]:
            print("[!] ZhipuAI selected but ZHIPUAI_API_KEY not set!")
            print("    Run: set ZHIPUAI_API_KEY=your_key")
            return
    elif CONFIG["ai_backend"] == "openai":
        if not CONFIG["openai_api_key"]:
            print("[!] OpenAI selected but OPENAI_API_KEY not set!")
            return
    elif CONFIG["ai_backend"] == "anthropic":
        if not CONFIG["anthropic_api_key"]:
            print("[!] Anthropic selected but ANTHROPIC_API_KEY not set!")
            return

    print()

    os.makedirs(CONFIG["output_dir"], exist_ok=True)

    # Find videos
    video_dir = Path(CONFIG["video_dir"])
    if not video_dir.exists():
        print(f"[!] Video directory not found: {video_dir}")
        return

    video_extensions = [".mp4", ".mov", ".avi", ".mkv"]
    video_files = []
    for ext in video_extensions:
        video_files.extend(video_dir.glob(f"*{ext}"))
        video_files.extend(video_dir.glob(f"*{ext.upper()}"))

    if not video_files:
        print(f"[!] No video files found in {video_dir}")
        return

    print(f"[*] Found {len(video_files)} video file(s)")

    # Process videos
    all_results = []
    for video_path in video_files:
        try:
            result = process_video(video_path)
            all_results.append(result)
        except Exception as e:
            print(f"[!] Error processing {video_path}: {e}")

    # Generate summary report
    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE")
    print(f"{'='*60}")

    summary = {
        "processed_at": datetime.now().isoformat(),
        "total_videos": len(all_results),
        "ai_backend": CONFIG["ai_backend"],
        "results": all_results
    }

    report_path = os.path.join(CONFIG["output_dir"], "report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Summary report saved to: {report_path}")
    print(f"[OK] Individual analyses saved in: {CONFIG['output_dir']}/<video_name>/analysis.json")

    # Print frame analyses
    for result in all_results:
        if "frame_analyses" in result:
            print(f"\n{'='*60}")
            print(f"FRAME ANALYSES FOR: {result['name']}")
            print(f"{'='*60}")
            for analysis in result["frame_analyses"]:
                print(f"\n--- Frame {analysis['frame']} ---")
                print(analysis["analysis"][:500] + "..." if len(analysis["analysis"]) > 500 else analysis["analysis"])

    print("\n[*] Done!")


if __name__ == "__main__":
    main()
