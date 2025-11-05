#!/usr/bin/env python3
"""
修复 dashscope API 调用问题
"""
import os
import re

def fix_processor():
    """修复 processor.py 中的 dashscope API 调用"""
    processor_file = "douyin_mcp_server1/processor.py"

    with open(processor_file, 'r') as f:
        content = f.read()

    # 找到问题代码段
    old_code = """                task_response = dashscope.audio.asr.Transcription.async_call(
                    model=self.model,
                    file=[audio_file],  # 使用本地文件
                    language_hints=['zh', 'en']
                )"""

    # 修复方案1：使用 file_urls 参数（如果需要先上传）
    new_code1 = """                # 需要先上传文件或使用正确的参数格式
                # 方案1：如果SDK要求file_urls
                task_response = dashscope.audio.asr.Transcription.async_call(
                    model=self.model,
                    file_urls=[f"file://{audio_file.name}"],  # 使用文件URL
                    language_hints=['zh', 'en']
                )"""

    # 修复方案2：使用正确的文件格式
    new_code2 = """                # 使用正确的API格式
                task_response = dashscope.audio.asr.Transcription.async_call(
                    model=self.model,
                    file_urls=[audio_file.name],  # 直接使用文件路径
                    language_hints=['zh', 'en'],
                    format='wav'  # 指定音频格式
                )"""

    # 修复方案3：使用文件对象但使用正确的参数名
    new_code3 = """                # 使用文件对象但正确处理
                import io

                # 读取文件内容
                audio_data = audio_file.read()
                audio_file.seek(0)

                # 创建一个临时文件名
                temp_filename = f"audio_{int(time.time())}.wav"

                # 尝试使用正确的API调用
                task_response = dashscope.audio.asr.Transcription.async_call(
                    model=self.model,
                    file=[(temp_filename, audio_data)],  # 使用文件元组
                    language_hints=['zh', 'en']
                )"""

    # 简单的修复：将 file 改为 file_urls
    if 'file=[audio_file]' in content:
        print("找到问题代码，进行修复...")
        content = content.replace(
            'file=[audio_file]',
            'file_urls=[audio_file.name]'
        )

        with open(processor_file, 'w') as f:
            f.write(content)

        print("✅ 已修复 processor.py")
        return True
    else:
        print("未找到问题代码，可能已经修复或使用了不同版本")
        return False

def check_dashscope_documentation():
    """检查 dashscope 的正确用法"""
    print("\nDashscope API 使用说明：")
    print("=" * 60)
    print("""
根据错误信息，dashscope SDK 期望的是 file_urls 参数。

正确的调用方式应该是：

1. 对于本地文件：
   Transcription.async_call(
       model='paraformer-realtime-v1',
       file_urls=['/path/to/audio.wav'],
       language_hints=['zh', 'en']
   )

2. 对于网络文件：
   Transcription.async_call(
       model='paraformer-realtime-v1',
       file_urls=['https://example.com/audio.wav'],
       language_hints=['zh', 'en']
   )

3. 如果SDK版本较新，可能需要：
   Transcription.async_call(
       model='paraformer-realtime-v1',
       file=[('filename.wav', file_object)],
       language_hints=['zh', 'en']
   )

建议：
1. 检查 dashscope 版本：pip show dashscope
2. 查看最新文档：https://help.aliyun.com/zh/dashscope/developer-reference/api-details
    """)

if __name__ == "__main__":
    print("分析 dashscope API 调用错误...")
    print("\n错误原因：")
    print("- Transcription.async_call() 需要 file_urls 参数而不是 file 参数")
    print("- 这可能是 SDK 版本更新导致的 API 变化")

    # 尝试修复
    if fix_processor():
        print("\n修复完成！")
    else:
        print("\n需要手动检查代码")

    check_dashscope_documentation()