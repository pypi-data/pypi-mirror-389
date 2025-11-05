#!/usr/bin/env python3
"""直接测试 MCP 工具列表"""
import json
import sys
import subprocess

# 测试本地代码
print("=== 测试本地 __init__.py ===")
sys.path.insert(0, '/app/test/douyin-mcp-server')

from douyin_mcp_server1 import handle_mcp_request

# 构造 tools/list 请求
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
}

response = handle_mcp_request(request)
print(f"响应: {json.dumps(response, indent=2, ensure_ascii=False)}")

if response and 'result' in response:
    tools = response['result'].get('tools', [])
    print(f"\n工具数量: {len(tools)}")
    for tool in tools:
        print(f"- {tool['name']}: {tool['description']}")

print("\n" + "="*50)

# 测试 mcp_server_simple.py
print("\n=== 测试 mcp_server_simple.py ===")
try:
    result = subprocess.run(
        ['python3', '-m', 'douyin_mcp_server1.mcp_server_simple'],
        input='{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n',
        capture_output=True,
        text=True,
        cwd='/app/test/douyin-mcp-server'
    )
    print(f"返回码: {result.returncode}")
    print(f"输出: {result.stdout}")
    if result.stderr:
        print(f"错误: {result.stderr}")
except Exception as e:
    print(f"错误: {e}")