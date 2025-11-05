#!/usr/bin/env python3
"""验证6个工具"""
import json
import subprocess

result = subprocess.run(
    ['cat', 'test_input.json'],
    stdout=subprocess.PIPE,
    text=True
)

process = subprocess.run(
    ['python', '-m', 'douyin_mcp_server1.mcp_server_simple'],
    input=result.stdout,
    capture_output=True,
    text=True
)

response = json.loads(process.stdout)
tools = response['result']['tools']

print(f"工具数量: {len(tools)}")
print("\n工具列表:")
for i, tool in enumerate(tools, 1):
    print(f"{i}. {tool['name']}")
    print(f"   描述: {tool['description']}")

# 测试工具调用
print("\n" + "="*50)
print("测试 extract_douyin_text 工具调用...")

test_request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "extract_douyin_text",
        "arguments": {
            "share_link": "https://v.douyin.com/test123",
            "model": "paraformer-realtime-v1"
        }
    }
}

process2 = subprocess.run(
    ['python', '-m', 'douyin_mcp_server1.mcp_server_simple'],
    input=json.dumps(test_request) + '\n',
    capture_output=True,
    text=True
)

response2 = json.loads(process2.stdout)
print(f"响应: {json.dumps(response2, indent=2, ensure_ascii=False)}")