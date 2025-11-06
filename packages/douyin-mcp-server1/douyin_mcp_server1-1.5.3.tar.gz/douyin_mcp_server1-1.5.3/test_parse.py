#!/usr/bin/env python3
"""测试视频解析功能"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'douyin_mcp_server1'))

from server_fastmcp_real import parse_share_url

# 测试数据
share_text = "1.74 o@D.hO nQk:/ 04/24 只讲干货，十五五规划到底说了啥？ # 我在十四五这五年 # 零距离看懂财经  https://v.douyin.com/cGF6wYr0cok/ 复制此链接，打开Dou音搜索，直接观看视频！"

print("测试抖音视频解析...")
print(f"输入: {share_text[:100]}...\n")

result = parse_share_url(share_text)

print("解析结果:")
print(f"- 视频ID: {result.get('video_id')}")
print(f"- 标题: {result.get('title')}")
print(f"- URL: {result.get('url')[:80] if result.get('url') else None}...")
print(f"- 错误: {result.get('error', 'None')}")