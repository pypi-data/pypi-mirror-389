#!/usr/bin/env python3
"""
测试最小化服务器
"""
import subprocess
import json
import sys
import time

def test_minimal_server():
    """测试最小化服务器"""
    print("=== 测试最小化服务器 ===")

    # 1. 直接运行
    print("\n1. 直接运行测试...")
    proc = subprocess.Popen(
        [sys.executable, "minimal_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={"DASHSCOPE_API_KEY": "test_key"}
    )

    # 发送初始化
    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }

    try:
        proc.stdin.write(json.dumps(init_msg) + "\n")
        proc.stdin.flush()

        # 等待响应
        start_time = time.time()
        response = None
        while time.time() - start_time < 3:
            if proc.poll() is not None:
                break
            line = proc.stdout.readline()
            if line:
                response = line.strip()
                break

        if response:
            data = json.loads(response)
            if "result" in data:
                print("✅ 直接运行成功")
            else:
                print(f"❌ 响应错误: {data}")
        else:
            print("❌ 没有响应")

        # 读取错误信息
        stderr = proc.stderr.read()
        if stderr:
            print(f"错误输出:\n{stderr}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        proc.terminate()

if __name__ == "__main__":
    test_minimal_server()
