#!/usr/bin/env python3
"""
测试音频压缩功能
"""
import os
import tempfile
import ffmpeg
from pathlib import Path

def create_test_audio(duration=60, output_path="test_audio.mp3"):
    """创建测试音频文件"""
    try:
        # 生成一个60秒的测试音频
        (
            ffmpeg
            .input('anullsrc=r=44100:cl=stereo', f='lavfi', t=duration)
            .output(output_path, acodec='libmp3lame', audio_bitrate='320k')
            .run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
        )

        file_size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        print(f"测试音频已创建: {output_path}")
        print(f"大小: {file_size_mb:.2f} MB")
        print(f"时长: {duration} 秒")

        return Path(output_path)

    except Exception as e:
        print(f"创建测试音频失败: {e}")
        return None

if __name__ == "__main__":
    # 测试创建音频
    audio_file = create_test_audio(duration=300)  # 5分钟
    if audio_file:
        print("\n测试完成！")
        # 清理
        audio_file.unlink()
        print("测试文件已清理")