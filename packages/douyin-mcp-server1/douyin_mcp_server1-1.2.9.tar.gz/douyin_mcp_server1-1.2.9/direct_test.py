#!/usr/bin/env python3
"""
直接测试 MCP 服务器启动
"""
import subprocess
import json
import sys
import time

def test_direct():
    """直接测试"""
    print("直接测试 MCP 服务器...")

    # 启动我们的简化版本
    cmd = [sys.executable, "-c", """
from douyin_mcp_server1.mcp_server_simple import main
main()
"""]

    print(f"执行命令: {' '.join(cmd)}")

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={"DASHSCOPE_API_KEY": "test_key"}
    )

    # 等待一下让服务器启动
    time.sleep(1)

    # 检查进程是否还在运行
    poll = proc.poll()
    print(f"进程状态: {poll}")

    # 如果已经退出，读取错误信息
    if poll is not None:
        print("进程已退出")
        stderr = proc.stderr.read()
        if stderr:
            print(f"错误输出:\n{stderr}")
        return False

    # 发送初始化请求
    print("\n发送初始化请求...")
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

    try:
        proc.stdin.write(json.dumps(init_request))
        proc.stdin.write("\n")
        proc.stdin.flush()

        print("请求已发送，等待响应...")

        # 等待响应
        start_time = time.time()
        while time.time() - start_time < 5:
            # 使用 select 检查是否有输出
            import select
            if select.select([proc.stdout], [], [], 0.1)[0]:
                line = proc.stdout.readline()
                if line:
                    print(f"收到响应: {line.strip()}")
                    try:
                        data = json.loads(line.strip())
                        if "result" in data:
                            print("✅ 成功！")
                            proc.terminate()
                            return True
                    except:
                        print("JSON 解析失败")
                break

            # 检查进程是否还在运行
            poll = proc.poll()
            if poll is not None:
                print(f"进程退出，返回码: {poll}")
                stderr = proc.stderr.read()
                if stderr:
                    print(f"错误输出:\n{stderr}")
                break

    except Exception as e:
        print(f"错误: {e}")
        proc.terminate()
        return False

    print("超时或没有收到有效响应")
    proc.terminate()
    return False

if __name__ == "__main__":
    test_direct()