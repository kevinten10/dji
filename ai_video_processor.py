"""
DJI 无人机视频 AI 全自动处理脚本
基于智谱 AI (GLM-4V) + FFmpeg

使用前请先安装依赖：
pip install zhipuai opencv-python tqdm

并设置环境变量：
export ZHIPUAI_API_KEY="your-api-key"
"""

import os
import sys
import json
import subprocess
import base64
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# 尝试导入智谱 AI SDK
try:
    from zhipuai import ZhipuAI
    HAS_ZHIPUAI = True
except ImportError:
    HAS_ZHIPUAI = False
    print("⚠️ 未安装 zhipuai，请运行: pip install zhipuai")

# ============ 配置区 ============
CONFIG = {
    # 智谱 AI API Key (请替换为你的)
    "api_key": os.getenv("ZHIPUAI_API_KEY", "YOUR_API_KEY_HERE"),

    # 视频文件夹路径
    "video_dir": "./videos",

    # 输出文件夹
    "output_dir": "./output",

    # 每个视频提取的帧数（用于 AI 分析）
    "num_frames": 6,

    # 视频片段时长（秒）
    "clip_duration": 5,

    # 视频质量 (CRF 值，越低越高)
    "quality": 23,

    # 是否启用 AI 分析
    "enable_ai_analysis": True,

    # 是否自动剪辑
    "enable_auto_edit": True,

    # 是否生成配音
    "enable_tts": False,
}

# ============ 工具函数 ============

def run_cmd(cmd, description=""):
    """执行系统命令"""
    if description:
        print(f"🔧 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️ 命令执行失败: {cmd}")
        print(f"错误: {result.stderr}")
        return False
    return True


def extract_frames(video_path, output_dir, num_frames=6):
    """从视频中均匀提取帧"""
    print(f"\n📸 正在提取帧: {video_path}")

    os.makedirs(output_dir, exist_ok=True)

    # 获取视频时长
    cmd = f'ffprobe -v quiet -show_entries format=duration -of json "{video_path}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    duration = float(data['format']['duration'])

    # 计算提取时间点
    interval = duration / (num_frames + 1)
    timestamps = [interval * (i + 1) for i in range(num_frames)]

    frames = []
    for i, ts in enumerate(timestamps):
        output_path = os.path.join(output_dir, f"frame_{i:03d}.jpg")
        cmd = f'ffmpeg -ss {ts} -i "{video_path}" -vframes 1 -y "{output_path}"'
        if run_cmd(cmd, f"提取帧 {i+1}/{num_frames} (时间: {ts:.1f}s)"):
            frames.append(output_path)

    return frames


def encode_image_base64(image_path):
    """将图片转为 base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def analyze_frames_with_glm(frames, api_key):
    """使用 GLM-4V 分析视频帧"""
    if not HAS_ZHIPUAI:
        print("⚠️ 无法分析：zhipuai 未安装")
        return None

    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("⚠️ 请设置 ZHIPUAI_API_KEY 环境变量")
        return None

    print("\n🤖 正在使用 GLM-4V 分析视频内容...")

    try:
        client = ZhipuAI(api_key=api_key)

        # 构造多轮对话
        messages = [
            {
                "role": "user",
                "content": [
                    "你是一个专业的航拍视频剪辑师。请分析这些视频帧，告诉我：",
                    "1. 视频主要内容是什么（风景/建筑/人物等）？",
                    "2. 视频的风格和氛围（宁静/震撼/活泼等）？",
                    "3. 视频的最佳使用场景？",
                    "请用简洁的中文回答。"
                ]
            }
        ]

        # 添加图片
        for frame in frames:
            img_base64 = encode_image_base64(frame)
            messages[0]["content"].append({
                "image": img_base64,
                "type": "image"
            })

        response = client.chat.completions.create(
            model="glm-4v",
            messages=messages,
            temperature=0.7,
        )

        analysis = response.choices[0].message.content
        print(f"\n📝 AI 分析结果:\n{analysis}")
        return analysis

    except Exception as e:
        print(f"⚠️ AI 分析失败: {e}")
        return None


def generate_script_with_glm(analysis, api_key):
    """使用 GLM-4 生成视频脚本/文案"""
    if not HAS_ZHIPUAI:
        return None

    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return None

    print("\n✍️ 正在使用 GLM-4 生成视频脚本...")

    try:
        client = ZhipuAI(api_key=api_key)

        prompt = f"""你是一个专业的航拍视频剪辑师和文案撰写师。

根据以下视频分析，为这个航拍视频生成：
1. 一个吸引人的标题（15字以内）
2. 一段 30-60 秒的解说词（100-150字）
3. 3-5 个适合的标签（用 # 开头）

视频分析内容：
{analysis}

请以 JSON 格式输出：
{{
    "title": "标题",
    "script": "解说词内容",
    "tags": ["#标签1", "#标签2", "#标签3"]
}}

只输出 JSON，不要其他内容。"""

        response = client.chat.completions.create(
            model="glm-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )

        result_text = response.choices[0].message.content
        # 尝试解析 JSON
        try:
            result = json.loads(result_text)
            print(f"\n🎬 生成的标题: {result.get('title', '')}")
            print(f"\n📜 解说词:\n{result.get('script', '')}")
            print(f"\n🏷️ 标签: {', '.join(result.get('tags', []))}")
            return result
        except:
            print(f"\n⚠️ JSON 解析失败，原始输出:\n{result_text}")
            return None

    except Exception as e:
        print(f"⚠️ 脚本生成失败: {e}")
        return None


def auto_clip_video(video_path, output_path, clip_duration=5):
    """自动剪辑视频 - 提取最佳片段"""
    print(f"\n✂️ 正在自动剪辑视频...")

    # 获取视频信息
    cmd = f'ffprobe -v quiet -show_entries format=duration -of json "{video_path}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    duration = float(data['format']['duration'])

    # 计算片段数量
    num_clips = max(1, int(duration / clip_duration))

    clips_dir = os.path.join(os.path.dirname(output_path), "clips")
    os.makedirs(clips_dir, exist_ok=True)

    clip_paths = []
    for i in range(num_clips):
        start_time = i * clip_duration
        clip_path = os.path.join(clips_dir, f"clip_{i:03d}.mp4")

        cmd = f'''ffmpeg -ss {start_time} -i "{video_path}" -t {clip_duration} \
                  -c:v libx264 -crf {CONFIG["quality"]} -c:a aac -y "{clip_path}"'''

        if run_cmd(cmd, f"剪辑片段 {i+1}/{num_clips}"):
            clip_paths.append(clip_path)

    # 合并所有片段
    if len(clip_paths) > 1:
        concat_list = os.path.join(clips_dir, "concat.txt")
        with open(concat_list, 'w') as f:
            for clip in clip_paths:
                f.write(f"file '{clip}'\n")

        cmd = f'ffmpeg -f concat -safe 0 -i "{concat_list}" -c copy -y "{output_path}"'
        run_cmd(cmd, "合并所有片段")
    elif len(clip_paths) == 1:
        import shutil
        shutil.copy(clip_paths[0], output_path)

    return output_path


def add_subtitles(video_path, output_path, subtitles):
    """添加字幕到视频"""
    if not subtitles:
        return video_path

    print("\n📝 正在添加字幕...")

    # 创建 SRT 字幕文件
    srt_path = output_path.replace('.mp4', '.srt')

    # 简单的字幕生成（需要根据实际语音长度调整）
    # 这里只是占位符
    duration = 5  # 每段 5 秒
    for i, line in enumerate(subtitles.split('\n')):
        if line.strip():
            start = datetime.strptime('00:00:00', '%H:%M:%S')
            start_time = (start + timedelta(seconds=i*duration)).strftime('%H:%M:%S')
            end_time = (start + timedelta(seconds=(i+1)*duration)).strftime('%H:%M:%S')

    # 使用 ffmpeg 添加字幕
    cmd = f'ffmpeg -i "{video_path}" -vf "subtitles={srt_path}" -y "{output_path}"'
    run_cmd(cmd, "烧录字幕")

    return output_path


def create_compilation(videos_dir, output_path):
    """将多个视频合并为一个合集"""
    print("\n🎬 正在创建视频合集...")

    video_files = sorted(Path(videos_dir).glob("*.mp4"))

    if not video_files:
        print("⚠️ 没有找到视频文件")
        return None

    # 创建合并列表
    concat_list = os.path.join(videos_dir, "concat.txt")
    with open(concat_list, 'w') as f:
        for video in video_files:
            f.write(f"file '{video.absolute()}'\n")

    # 合并视频
    cmd = f'ffmpeg -f concat -safe 0 -i "{concat_list}" -c:v libx264 -crf {CONFIG["quality"]} -c:a aac -y "{output_path}"'
    run_cmd(cmd, "合并视频")

    return output_path


def compress_video(video_path, output_path):
    """压缩视频"""
    print("\n🗜️ 正在压缩视频...")

    cmd = f'ffmpeg -i "{video_path}" -c:v libx264 -crf 28 -c:a aac -y "{output_path}"'
    run_cmd(cmd, "压缩完成")

    return output_path


# ============ 主流程 ============

def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║       DJI 无人机视频 AI 全自动处理工具                         ║
║       基于 智谱 AI (GLM) + FFmpeg                              ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    # 检查 FFmpeg
    if not run_cmd("ffmpeg -version", "检查 FFmpeg"):
        print("❌ 请先安装 FFmpeg: https://ffmpeg.org/download.html")
        return

    # 检查 API Key
    api_key = CONFIG["api_key"]
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("❌ 请设置智谱 AI API Key:")
        print("   Windows: set ZHIPUAI_API_KEY=你的API密钥")
        print("   Mac/Linux: export ZHIPUAI_API_KEY=你的API密钥")
        print("\n   或直接编辑脚本修改 CONFIG['api_key']")
        return

    # 创建输出目录
    os.makedirs(CONFIG["output_dir"], exist_ok=True)

    # 查找视频文件
    video_files = sorted(Path(CONFIG["video_dir"]).glob("*.MP4"))
    if not video_files:
        video_files = sorted(Path(CONFIG["video_dir"]).glob("*.mp4"))

    if not video_files:
        print(f"❌ 在 {CONFIG['video_dir']} 中没有找到视频文件")
        return

    print(f"\n📁 找到 {len(video_files)} 个视频文件:")
    for i, v in enumerate(video_files):
        print(f"   {i+1}. {v.name}")

    # 处理每个视频
    all_analysis = []
    all_scripts = []

    for video_file in video_files:
        print(f"\n{'='*60}")
        print(f"🎬 正在处理: {video_file.name}")
        print('='*60)

        video_name = video_file.stem
        video_output_dir = os.path.join(CONFIG["output_dir"], video_name)
        os.makedirs(video_output_dir, exist_ok=True)

        # 1. 提取帧
        frames_dir = os.path.join(video_output_dir, "frames")
        frames = extract_frames(str(video_file), frames_dir, CONFIG["num_frames"])

        # 2. AI 分析
        if CONFIG["enable_ai_analysis"] and HAS_ZHIPUAI:
            analysis = analyze_frames_with_glm(frames, api_key)
            if analysis:
                all_analysis.append(analysis)

                # 3. 生成脚本
                script = generate_script_with_glm(analysis, api_key)
                if script:
                    all_scripts.append(script)

                    # 保存分析结果
                    with open(os.path.join(video_output_dir, "analysis.json"), 'w', encoding='utf-8') as f:
                        json.dump({
                            "analysis": analysis,
                            "script": script
                        }, f, ensure_ascii=False, indent=2)

        # 4. 自动剪辑
        if CONFIG["enable_auto_edit"]:
            clipped_path = os.path.join(video_output_dir, "clipped.mp4")
            auto_clip_video(str(video_file), clipped_path, CONFIG["clip_duration"])

    # 5. 创建合集（如果有多个视频）
    if len(video_files) > 1:
        compilation_path = os.path.join(CONFIG["output_dir"], "compilation.mp4")
        create_compilation(CONFIG["output_dir"], compilation_path)

    # 6. 生成最终报告
    print(f"\n{'='*60}")
    print("📊 处理完成！")
    print('='*60)
    print(f"\n📁 输出目录: {CONFIG['output_dir']}")
    print(f"\n✨ 建议的下一步:")
    print("   1. 查看 analysis.json 查看 AI 分析结果")
    print("   2. 使用剪映/花生AI 导入 clipped.mp4 进行精细剪辑")
    print("   3. 或上传到一帧秒创添加配音和字幕")

    # 保存总体报告
    report = {
        "video_count": len(video_files),
        "videos": [str(v) for v in video_files],
        "analysis": all_analysis,
        "scripts": all_scripts,
        "timestamp": datetime.now().isoformat()
    }

    with open(os.path.join(CONFIG["output_dir"], "report.json"), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📋 完整报告已保存到: {CONFIG['output_dir']}/report.json")


if __name__ == "__main__":
    main()
