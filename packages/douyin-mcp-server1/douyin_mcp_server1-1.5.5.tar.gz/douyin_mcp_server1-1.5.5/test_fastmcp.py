#!/usr/bin/env python3
"""测试 FastMCP 服务器"""

import subprocess
import json
import sys

def test_fastmcp():
    proc = subprocess.Popen(
        ["python", "douyin_mcp_server1/server_fastmcp_real.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 1. 初始化
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test",
                "version": "1.0"
            }
        }
    }

    proc.stdin.write(json.dumps(init_request) + "\n")
    proc.stdin.flush()

    # 读取初始化响应
    response = proc.stdout.readline()
    print("Init response:", response)

    # 2. 发送 initialized 通知
    init_notify = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }

    proc.stdin.write(json.dumps(init_notify) + "\n")
    proc.stdin.flush()

    # 3. 列出工具
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }

    proc.stdin.write(json.dumps(tools_request) + "\n")
    proc.stdin.flush()

    # 读取工具列表响应
    response = proc.stdout.readline()
    print("Tools response:", response)

    # 解析并美化输出
    try:
        data = json.loads(response)
        if "result" in data and "tools" in data["result"]:
            print(f"\n找到 {len(data['result']['tools'])} 个工具:")
            for tool in data["result"]["tools"]:
                print(f"  - {tool['name']}: {tool['description']}")
    except:
        pass

    proc.terminate()

if __name__ == "__main__":
    test_fastmcp()