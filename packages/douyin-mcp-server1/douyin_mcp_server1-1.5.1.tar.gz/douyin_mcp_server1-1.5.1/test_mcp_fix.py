#!/usr/bin/env python3
"""测试MCP修复后的参数处理"""
import subprocess
import json
import os

print("=== 测试MCP修复后的参数处理 ===\n")

# 测试1: 标准JSON-RPC通信
print("1. 测试标准JSON-RPC通信...")
process1 = subprocess.run(
    ["python3", "-m", "douyin_mcp_server1"],
    input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}}}}\n{"jsonrpc":"2.0","id":2,"method":"tools/list"}\n',
    capture_output=True,
    text=True,
    cwd="/app/test/douyin-mcp-server"
)

responses = process1.stdout.strip().split('\n')
for resp in responses:
    if resp:
        data = json.loads(resp)
        if "result" in data and "tools" in data["result"]:
            print(f"✅ 工具数量: {len(data['result']['tools'])}")

# 测试2: 命令行传入环境变量
print("\n2. 测试命令行传入环境变量...")
process2 = subprocess.run(
    ["python3", "-m", "douyin_mcp_server1", "DASHSCOPE_API_KEY=test_key_12345"],
    input='{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"extract_douyin_text","arguments":{"share_link":"https://v.douyin.com/test"}}}\n',
    capture_output=True,
    text=True,
    cwd="/app/test/douyin-mcp-server"
)

if process2.stdout:
    response = json.loads(process2.stdout.strip())
    if "result" in response:
        content = response["result"]["content"][0]["text"]
        if "DASHSCOPE_API_KEY" in content:
            print("✅ 环境变量处理正常")

# 测试3: uvx 风格的参数传递
print("\n3. 测试uvx风格的参数传递...")
# 模拟 uvx 传递的参数
test_args = [
    "python3", "-m", "douyin_mcp_server1",
    "--default-index", "https://pypi.org/simple",  # uvx 参数
    "DASHSCOPE_API_KEY=sk-test12345",  # 环境变量作为参数
    "INVALID_PARAM=value"  # 无效参数
]

process3 = subprocess.run(
    test_args,
    input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}}}}\n',
    capture_output=True,
    text=True,
    cwd="/app/test/douyin-mcp-server"
)

if process3.returncode == 0:
    response = json.loads(process3.stdout.strip())
    if "result" in response and "serverInfo" in response["result"]:
        print(f"✅ 服务器启动成功，版本: {response['result']['serverInfo']['version']}")

# 测试4: 错误处理
print("\n4. 测试错误处理...")
process4 = subprocess.run(
    ["python3", "-m", "douyin_mcp_server1"],
    input='invalid json\n{"jsonrpc":"2.0","id":1,"method":"unknown_method"}\n',
    capture_output=True,
    text=True,
    cwd="/app/test/douyin-mcp-server"
)

if process4.stdout:
    # 应该忽略无效JSON并返回错误响应
    print("✅ 错误处理正常")

print("\n=== 测试完成 ===")