#!/usr/bin/env python3
"""
直接测试 uvx 调用
"""
import subprocess
import json
import sys
import time

def test_uvx_direct():
    """直接测试 uvx 调用"""
    print("直接测试 uvx 调用 douyin-mcp-server1==1.2.2...")

    # 启动 uvx
    cmd = ["uvx", "--verbose", "douyin-mcp-server1==1.2.2"]

    print(f"执行命令: {' '.join(cmd)}")

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={"DASHSCOPE_API_KEY": "test_key"}
    )

    try:
        # 等待启动
        time.sleep(3)

        # 读取一些输出
        print("\n=== 读取前10行 stderr ===")
        stderr_lines = []
        for i in range(10):
            line = proc.stderr.readline()
            if not line:
                break
            stderr_lines.append(line)
            print(f"{i+1}: {line.strip()}")

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

        print("\n发送初始化请求...")
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        # 等待响应
        time.sleep(2)

        # 读取响应
        print("\n=== 读取 stdout ===")
        response = proc.stdout.readline()
        if response:
            print(f"响应: {response.strip()}")
            try:
                data = json.loads(response.strip())
                if "result" in data:
                    print("✅ 初始化成功!")
                else:
                    print("❌ 初始化失败")
                    print(f"错误: {data}")
            except:
                print("❌ JSON 解析失败")
        else:
            print("❌ 没有收到响应")

        # 继续读取更多错误信息
        print("\n=== 继续读取 stderr ===")
        for i in range(10):
            line = proc.stderr.readline()
            if not line:
                break
            print(f"{i+1}: {line.strip()}")

        proc.terminate()

    except Exception as e:
        print(f"错误: {e}")
        proc.terminate()

if __name__ == "__main__":
    test_uvx_direct()