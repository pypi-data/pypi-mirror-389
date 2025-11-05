#!/usr/bin/env python3
"""
测试 uvx 本地安装
"""
import subprocess
import json
import sys
import time

def test_uvx_local():
    """测试 uvx 本地运行"""
    print("测试 uvx 本地运行 MCP 服务器...")

    # 构建 wheel 文件的完整路径
    wheel_path = "/app/test/douyin-mcp-server/dist/douyin_mcp_server1-1.2.2-py3-none-any.whl"

    # 使用 uvx 运行本地 wheel
    cmd = ["uvx", wheel_path]

    print(f"执行命令: {' '.join(cmd)}")

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 等待启动
        time.sleep(2)

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
        if response:
            data = json.loads(response.strip())
            if "result" in data:
                print("✅ uvx 本地运行成功!")
                proc.terminate()
                return True
            else:
                print(f"❌ 初始化失败: {data}")
                stderr = proc.stderr.read()
                if stderr:
                    print(f"错误: {stderr}")
        else:
            print("❌ 没有响应")

        proc.terminate()
        return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_uvx_local()