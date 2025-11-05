#!/usr/bin/env python3
"""
测试调试版服务器
"""
import subprocess
import json
import sys
import time

def test_debug_server():
    """测试调试版服务器"""
    print("测试调试版 MCP 服务器...")

    # 设置环境变量
    env = os.environ.copy()
    env["DASHSCOPE_API_KEY"] = "test_key"

    # 启动服务器
    proc = subprocess.Popen(
        [sys.executable, "-m", "douyin_mcp_server1.mcp_server_debug"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )

    try:
        # 等待服务器启动
        time.sleep(1)

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

        # 读取调试信息
        print("\n=== 调试输出 (stderr) ===")
        stderr_lines = []
        start_time = time.time()

        while time.time() - start_time < 5:  # 5秒超时
            line = proc.stderr.readline()
            if line:
                print(line.strip())
                stderr_lines.append(line)

            # 尝试读取 stdout
            try:
                sys.stdout.write("检查 stdout...\n")
                sys.stdout.flush()

                # 使用 select 检查是否有数据
                import select
                if select.select([proc.stdout], [], [], 0.1)[0]:
                    response = proc.stdout.readline()
                    if response:
                        print(f"\n收到响应: {response.strip()}")
                        data = json.loads(response.strip())
                        if "result" in data:
                            print("✅ 初始化成功!")
                            proc.terminate()
                            return True
            except:
                pass

        print("\n❌ 超时或没有收到响应")

        # 读取所有错误输出
        remaining = proc.stderr.read()
        if remaining:
            print("\n剩余错误输出:")
            print(remaining)

        proc.terminate()
        return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        proc.terminate()
        return False


if __name__ == "__main__":
    import os
    test_debug_server()