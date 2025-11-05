#!/usr/bin/env python3
"""
测试入口点
"""
import subprocess
import json
import sys

def test_entry_point():
    """测试脚本入口点"""
    print("测试 douyin-mcp-server1 脚本...")

    # 模拟脚本调用
    proc = subprocess.Popen(
        [sys.executable, "-c", "import douyin_mcp_server1; douyin_mcp_server1.main()"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 发送请求
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
    if response:
        print(f"响应: {response.strip()}")
        data = json.loads(response.strip())
        if "result" in data:
            print("✅ 入口点测试成功!")
            proc.terminate()
            return True

    # 读取错误
    stderr = proc.stderr.read()
    if stderr:
        print(f"错误: {stderr}")

    proc.terminate()
    return False

if __name__ == "__main__":
    test_entry_point()