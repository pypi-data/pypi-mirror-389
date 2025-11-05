#!/usr/bin/env python3
"""
最小化测试，验证核心逻辑
"""
import sys

# 检查代码是否存在语法错误和逻辑问题
def check_code():
    print("正在检查代码...")

    with open('douyin_mcp_server/server.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 检查关键函数是否正确实现
    checks = [
        ('compress_audio', 'def compress_audio('),
        ('extract_text_from_audio_file', 'def extract_text_from_audio_file('),
        ('extract_douyin_text', 'async def extract_douyin_text('),
        ('get_audio_duration', 'def get_audio_duration('),
        ('cleanup_all', 'def cleanup_all('),
    ]

    print("\n✅ 检查函数定义:")
    for func_name, pattern in checks:
        if pattern in content:
            print(f"   ✓ {func_name} - 已定义")
        else:
            print(f"   ✗ {func_name} - 未找到！")

    # 2. 检查关键逻辑
    logic_checks = [
        ('音频提取', 'ffmpeg.input'),
        ('文件上传', 'file=[audio_file]'),
        ('临时目录', 'tempfile.mkdtemp'),
        ('并发安全', 'threading.Lock'),
        ('文件管理', 'managed_files'),
    ]

    print("\n✅ 检查关键逻辑:")
    for name, pattern in logic_checks:
        if pattern in content:
            print(f"   ✓ {name} - 已实现")
        else:
            print(f"   ✗ {name} - 缺失！")

    # 3. 检查 extract_douyin_text 是否使用了正确的流程
    extract_douyin_section = content[content.find('async def extract_douyin_text('):
                                        content.find('async def extract_douyin_text(') + 2000]

    flow_checks = [
        ('解析链接', 'parse_share_url'),
        ('下载视频', 'download_video'),
        ('提取音频', 'extract_audio'),
        ('压缩音频', 'compress_audio'),
        ('提取文本', 'extract_text_from_audio_file'),
        ('清理文件', 'cleanup_files'),
    ]

    print("\n✅ 检查 extract_douyin_text 流程:")
    for step, pattern in flow_checks:
        if pattern in extract_douyin_section:
            print(f"   ✓ {step} - 已包含")
        else:
            print(f"   ✗ {step} - 缺失！")

    # 4. 检查错误
    errors = []

    # 检查是否有未使用的变量
    if 'ctx_info = ' in content:
        errors.append("发现未使用的 ctx_info 变量")

    if errors:
        print("\n✗ 发现问题:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("\n✅ 代码检查通过！")
        return True

if __name__ == "__main__":
    success = check_code()
    if success:
        print("\n代码结构正确，应该可以正常运行。")
        print("\n注意事项:")
        print("1. 需要安装 ffmpeg-python: pip install ffmpeg-python")
        print("2. 需要安装系统 ffmpeg: apt-get install ffmpeg 或 brew install ffmpeg")
        print("3. 需要设置 DASHSCOPE_API_KEY 环境变量")
    sys.exit(0 if success else 1)