#!/usr/bin/env python3
"""调试音频API调用问题"""

import tempfile
import os
import json

def test_file_urls():
    """测试不同的文件URL格式"""

    # 创建测试音频文件
    temp_dir = tempfile.mkdtemp(prefix="debug_test_")
    test_audio = os.path.join(temp_dir, "test.wav")

    # 创建一个空的wav文件头
    with open(test_audio, 'wb') as f:
        f.write(b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00')
        f.write(b'\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00')

    print(f"创建测试文件: {test_audio}")
    print(f"文件大小: {os.path.getsize(test_audio)} bytes")
    print(f"文件存在: {os.path.exists(test_audio)}")

    # 测试不同的URL格式
    formats = {
        "直接路径": str(test_audio),
        "file:// 单斜杠": f"file://{test_audio}",
        "file:// 三斜杠": f"file:///{test_audio}",
        "file:// 四斜杠": f"file:////{test_audio}",
    }

    print("\n不同的文件URL格式:")
    for name, url in formats.items():
        print(f"{name}: {url}")

        # 测试是否能被正确解析
        try:
            from pathlib import Path
            path = Path(url.replace('file://', ''))
            print(f"  -> 解析路径: {path}")
            print(f"  -> 是否存在: {path.exists()}")
        except Exception as e:
            print(f"  -> 解析错误: {e}")

    # 清理
    os.unlink(test_audio)
    os.rmdir(temp_dir)

    return formats

def check_dashscope_documentation():
    """查看Dashscope文档中关于文件URL的要求"""
    print("\nDashscope API文件URL要求:")
    print("根据文档，file_urls应该:")
    print("1. 使用绝对路径")
    print("2. 可以使用 file:// 协议前缀")
    print("3. 确保文件对API可访问")

    print("\n正确格式示例:")
    print("- Linux/Mac: file:///absolute/path/to/audio.wav")
    print("- Windows: file:///C:/path/to/audio.wav")

if __name__ == "__main__":
    print("=== 音频文件URL格式调试 ===")
    formats = test_file_urls()
    check_dashscope_documentation()

    print("\n=== 建议 ===")
    print("1. 使用 file:/// 加绝对路径（三个斜杠）")
    print("2. 确保文件存在且可读")
    print("3. 检查文件大小是否在限制内")
    print("4. 验证音频格式是否支持")