#!/usr/bin/env python3
"""简单测试API路径格式问题"""

import os

# 模拟不同的路径格式
test_file = "/tmp/test_audio.wav"

print("=== Dashscope API 路径格式测试 ===\n")

formats = {
    "普通路径": test_file,
    "绝对路径": os.path.abspath(test_file),
    "字符串路径": str(test_file),
    "file:// 单斜杠": f"file://{test_file}",
    "file:// 三斜杠": f"file:///{test_file}",
    "file:// 四斜杠": f"file:////{test_file}",
}

print("不同的路径格式：")
for name, path in formats.items():
    print(f"{name}: {path}")

print("\n=== 分析 ===")
print("根据错误 'url error, please check url！'，")
print("API期望的是URL格式，而不是普通文件路径。")
print("\n可能的原因：")
print("1. API版本更新改变了参数要求")
print("2. 生产环境vs测试环境的差异")
print("3. API密钥权限限制")

print("\n=== 建议的解决方案 ===")
print("1. 使用 file:/// 格式（三个斜杠）")
print("2. 或者上传文件到云存储后使用HTTP URL")
print("3. 检查API文档的版本差异")