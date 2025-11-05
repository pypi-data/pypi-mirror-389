#!/usr/bin/env python3
"""
调试工具列表问题
"""
import subprocess
import json
import sys

# 启动服务器
proc = subprocess.Popen(
    [sys.executable, "-m", "douyin_mcp_server1.mcp_server_simple"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# 发送初始化
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"}
    }
}

proc.stdin.write(json.dumps(init_request) + "\n")
proc.stdin.flush()

# 读取响应
response = proc.stdout.readline()
print("初始化响应:", response)

# 发送 initialized 通知
init_notify = {
    "jsonrpc": "2.0",
    "method": "notifications/initialized"
}
proc.stdin.write(json.dumps(init_notify) + "\n")
proc.stdin.flush()

# 测试工具列表
tools_request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
}
proc.stdin.write(json.dumps(tools_request) + "\n")
proc.stdin.flush()

# 读取工具列表响应
tools_response = proc.stdout.readline()
print("工具列表响应:", tools_response)

# 解析
try:
    data = json.loads(tools_response.strip())
    print(f"解析结果: {data}")
    tools = data.get("result", {}).get("tools", [])
    print(f"工具数量: {len(tools)}")
except:
    pass

proc.terminate()