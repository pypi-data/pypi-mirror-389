#!/usr/bin/env python3
"""
本地视频文件语音提取工具
"""

import os
import json
import tempfile
import subprocess
from pathlib import Path

def extract_audio_from_video(video_path: str):
    """从视频文件提取音频"""
    import ffmpeg

    temp_dir = tempfile.mkdtemp(prefix=f"video_{os.getpid()}_")
    audio_path = os.path.join(temp_dir, "audio.wav")

    try:
        # 提取音频
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, acodec='pcm_s16le', ac=1, ar='16000')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        # 检查音频文件大小
        audio_size = os.path.getsize(audio_path)
        if audio_size > 50 * 1024 * 1024:  # 50MB
            # 压缩音频
            compressed_audio = os.path.join(temp_dir, "audio_compressed.wav")
            (
                ffmpeg
                .input(audio_path)
                .output(compressed_audio, acodec='pcm_s16le', ac=1, ar='16000', audio_bitrate='64k')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            audio_path = compressed_audio

        return audio_path, temp_dir

    except Exception as e:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise e

def transcribe_audio(audio_path: str, api_key: str, model: str = "paraformer-realtime-v1"):
    """使用Dashscope进行语音识别"""
    import dashscope
    from dashscope.audio.asr import Transcription

    dashscope.api_key = api_key

    transcription = Transcription(
        model=model,
        file_urls=[f"file://{audio_path}"],
        language_hints=["zh", "zh-CN", "en"],
        formats=["txt"]
    )

    result = transcription.get_result()

    if result.status_code == '200' and result.output:
        return result.output['transcript_result']['text']
    else:
        raise Exception(f"语音识别失败: {result.message}")

def process_video_file(video_file_path: str, api_key: str, model: str = "paraformer-realtime-v1"):
    """处理视频文件"""
    try:
        # 检查文件是否存在
        if not os.path.exists(video_file_path):
            raise Exception(f"文件不存在: {video_file_path}")

        # 检查是否是视频文件
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']
        if not any(video_file_path.lower().endswith(ext) for ext in video_extensions):
            raise Exception("不支持的文件格式")

        # 提取音频
        audio_path, temp_dir = extract_audio_from_video(video_file_path)

        try:
            # 语音识别
            text = transcribe_audio(audio_path, api_key, model)

            return {
                "status": "success",
                "message": "语音提取成功",
                "extracted_text": text,
                "video_file": video_file_path,
                "model": model,
                "audio_size": f"{os.path.getsize(audio_path)/1024/1024:.2f}MB"
            }

        finally:
            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        return {
            "status": "error",
            "message": f"处理失败: {str(e)}",
            "video_file": video_file_path,
            "model": model
        }

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("用法: python extract_local_video.py <视频文件路径> <DASHSCOPE_API_KEY>")
        sys.exit(1)

    video_file = sys.argv[1]
    api_key = sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "paraformer-realtime-v1"

    result = process_video_file(video_file, api_key, model)
    print(json.dumps(result, ensure_ascii=False, indent=2))