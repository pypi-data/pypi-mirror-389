#!/usr/bin/env python3
"""测试Dashscope API调用"""

import os
import tempfile
import subprocess
from pathlib import Path

# 设置测试API密钥 - 需要真实的密钥才能测试
os.environ["DASHSCOPE_API_KEY"] = "sk-proj-test"  # 替换为真实密钥

def test_api_with_different_formats():
    """测试不同音频格式的API调用"""
    print("=== 测试Dashscope API音频格式兼容性 ===\n")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="dashscope_test_")

    try:
        # 1. 生成测试音频 - WAV格式
        wav_path = os.path.join(temp_dir, "test.wav")
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=5',
            '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le',
            '-y', wav_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ WAV文件生成成功: {wav_path}")
            print(f"   文件大小: {os.path.getsize(wav_path)} bytes")

            # 验证文件
            probe = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_format', wav_path],
                capture_output=True, text=True
            )
            if probe.returncode == 0:
                print("   文件格式: 有效WAV")
        else:
            print(f"❌ WAV文件生成失败: {result.stderr}")
            return

        # 2. 测试API调用 - 使用绝对路径
        print("\n=== 测试API调用 ===")

        try:
            import dashscope
            from dashscope.audio.asr import Transcription

            # 设置API密钥
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key or api_key == "sk-proj-test":
                print("⚠️ 需要真实的API密钥才能测试")
                print("请设置环境变量 DASHSCOPE_API_KEY")
                return

            dashscope.api_key = api_key

            # 创建转录对象
            transcription = Transcription()

            # 测试不同的路径格式
            test_paths = [
                ("绝对路径", os.path.abspath(wav_path)),
                ("字符串路径", str(wav_path)),
                ("Path对象", Path(wav_path)),
                ("file:// URI", f"file://{os.path.abspath(wav_path)}"),
            ]

            for name, path in test_paths:
                print(f"\n测试 {name}: {path}")
                try:
                    result = transcription.async_call(
                        model="paraformer-realtime-v1",
                        file_urls=[path],
                        language_hints=["zh", "en"],
                        formats=["txt"]
                    )

                    print(f"  状态码: {result.status_code}")
                    if hasattr(result, 'message'):
                        print(f"  消息: {result.message}")

                    if result.status_code == '200':
                        print("  ✅ 成功！")
                        if hasattr(result, 'output') and result.output:
                            print(f"  结果: {result.output}")
                        break
                    else:
                        print(f"  ❌ 失败")

                except Exception as e:
                    print(f"  ❌ 异常: {e}")

        except ImportError:
            print("❌ 无法导入dashscope，请安装: pip install dashscope")

    finally:
        # 清理
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)

def check_api_documentation():
    """检查API文档要求"""
    print("\n=== Dashscope API 文档要求 ===")
    print("1. file_urls 参数要求:")
    print("   - 必须是URL格式，支持 file:// 协议")
    print("   - 必须是绝对路径")
    print("   - Linux: file:///absolute/path/to/file")
    print("   - Windows: file:///C:/path/to/file")

    print("\n2. 支持的音频格式:")
    print("   - WAV (PCM编码)")
    print("   - MP3")
    print("   - M4A (AAC)")
    print("   - FLAC")

    print("\n3. 错误 'url error' 的可能原因:")
    print("   - 文件路径格式错误")
    print("   - 文件不存在或无法访问")
    print("   - 文件格式不支持")
    print("   - 文件大小超过限制")
    print("   - 网络问题（API无法访问本地文件）")

    print("\n4. 可能的解决方案:")
    print("   - 使用正确的 file:/// 格式（三个斜杠）")
    print("   - 确保文件权限正确")
    print("   - 尝试上传到云存储后使用HTTP URL")
    print("   - 使用较小的测试文件")

if __name__ == "__main__":
    test_api_with_different_formats()
    check_api_documentation()