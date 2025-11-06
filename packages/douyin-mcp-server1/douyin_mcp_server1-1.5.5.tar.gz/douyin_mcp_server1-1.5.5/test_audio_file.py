#!/usr/bin/env python3
"""测试生成的音频文件是否有效"""

import subprocess
import tempfile
import os

def check_audio_file(file_path):
    """使用ffprobe检查音频文件"""
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_format', '-show_streams', file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ 音频文件有效: {file_path}")
            print("\n文件信息:")
            for line in result.stdout.split('\n'):
                if 'codec_name' in line or 'sample_rate' in line or 'channels' in line or 'duration' in line:
                    print(f"  {line}")
            return True
        else:
            print(f"❌ 音频文件无效: {file_path}")
            print(f"错误: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 无法检查文件: {e}")
        return False

def test_wav_creation():
    """测试创建一个简单的WAV文件"""
    temp_dir = tempfile.mkdtemp()
    test_wav = os.path.join(temp_dir, "test.wav")

    # 使用ffmpeg生成测试音频
    cmd = [
        'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1',
        '-ar', '16000', '-ac', '1', '-y', test_wav
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ 测试WAV文件创建成功")
        check_audio_file(test_wav)
        return True
    else:
        print(f"❌ 创建测试WAV失败: {result.stderr}")
        # 清理
        if os.path.exists(test_wav):
            os.unlink(test_wav)
        os.rmdir(temp_dir)
        return False

def test_mp3_creation():
    """测试创建一个MP3文件"""
    temp_dir = tempfile.mkdtemp()
    test_mp3 = os.path.join(temp_dir, "test.mp3")

    # 使用ffmpeg生成测试MP3音频
    cmd = [
        'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1',
        '-acodec', 'libmp3lame', '-ar', '16000', '-ac', '2', '-y', test_mp3
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ 测试MP3文件创建成功")
        check_audio_file(test_mp3)
        return True
    else:
        print(f"❌ 创建测试MP3失败: {result.stderr}")
        # 清理
        if os.path.exists(test_mp3):
            os.unlink(test_mp3)
        os.rmdir(temp_dir)
        return False

if __name__ == "__main__":
    print("=== 音频文件测试 ===")
    test_wav_creation()
    print("\n" + "="*50 + "\n")
    test_mp3_creation()