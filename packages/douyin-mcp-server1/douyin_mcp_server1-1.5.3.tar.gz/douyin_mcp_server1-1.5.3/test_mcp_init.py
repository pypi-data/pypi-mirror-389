#!/usr/bin/env python3
"""
测试 MCP 服务器的完整初始化流程
"""

import subprocess
import json
import sys
import time

def test_mcp_server():
    # 使用 uvx 启动服务器
    cmd = [
        "uvx",
        "--default-index",
        "https://pypi.org/simple",
        "douyin-mcp-server1==1.4.4"
    ]

    env = {
        "DASHSCOPE_API_KEY": "sk-27ed62f0217240a38efcebff00eeee42"
    }

    print(f"启动命令: {' '.join(cmd)}")
    print(f"环境变量: {env}")

    try:
        # 启动进程
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**dict(os.environ), **env}
        )

        # 发送初始化请求
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        print(f"\n发送初始化请求: {json.dumps(init_request)}")

        # 发送请求
        request_str = json.dumps(init_request) + "\n"
        proc.stdin.write(request_str)
        proc.stdin.flush()

        # 读取响应（设置超时）
        try:
            stdout, stderr = proc.communicate(timeout=5)
            print(f"\n返回码: {proc.returncode}")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")

            # 分析 stdout 中的每一行
            if stdout:
                lines = stdout.strip().split('\n')
                for i, line in enumerate(lines):
                    try:
                        parsed = json.loads(line)
                        print(f"\n第 {i+1} 行 JSON 解析成功:")
                        print(json.dumps(parsed, indent=2, ensure_ascii=False))
                    except:
                        print(f"\n第 {i+1} 行不是有效 JSON: {line}")

        except subprocess.TimeoutExpired:
            proc.kill()
            print("进程超时，已终止")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import os
    test_mcp_server()