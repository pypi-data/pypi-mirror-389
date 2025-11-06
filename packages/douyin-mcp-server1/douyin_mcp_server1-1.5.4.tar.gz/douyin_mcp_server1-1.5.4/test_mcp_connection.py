#!/usr/bin/env python3
"""测试 MCP 服务器连接"""

import subprocess
import json
import sys
import time
import threading
import queue
import signal
import os

def test_mcp_server():
    print("=== MCP 服务器连接测试 ===\n")

    # 测试命令
    cmd = [
        "uvx",
        "--index-strategy",
        "unsafe-best-match",
        "--index-url",
        "https://pypi.org/simple",
        "--extra-index-url",
        "https://mirrors.aliyun.com/pypi/simple/",
        "douyin-mcp-server1==1.5.0"
    ]

    env = {
        "DASHSCOPE_API_KEY": "sk-test"
    }

    print(f"启动命令: {' '.join(cmd)}")
    print(f"环境变量: {env}\n")

    # 创建输出队列
    output_queue = queue.Queue()

    def output_reader(process, queue):
        """读取进程输出"""
        for line in iter(process.stdout.readline, b''):
            if line:
                try:
                    queue.put(line.decode('utf-8').strip())
                except:
                    queue.put(line.decode('utf-8', errors='ignore').strip())

    try:
        # 启动进程
        print("启动 MCP 服务器...")
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,  # 使用字节模式
            env={**dict(os.environ), **env}
        )

        # 启动输出读取线程
        output_thread = threading.Thread(target=output_reader, args=(proc, output_queue))
        output_thread.daemon = True
        output_thread.start()

        # 等待服务器启动
        print("等待服务器启动...")
        time.sleep(3)

        # 测试初始化
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

        print(f"\n发送初始化请求...")
        print(f"请求: {json.dumps(init_request, indent=2)}")

        # 发送请求
        request_json = json.dumps(init_request) + "\n"
        proc.stdin.write(request_json.encode('utf-8'))
        proc.stdin.flush()

        # 等待响应
        print("\n等待响应...")
        response_timeout = 10
        start_time = time.time()
        response = None

        while time.time() - start_time < response_timeout:
            try:
                if not output_queue.empty():
                    line = output_queue.get(timeout=1)
                    print(f"收到输出: {line}")

                    # 尝试解析JSON
                    try:
                        response = json.loads(line)
                        if response.get("id") == 1:
                            print(f"\n✓ 收到初始化响应!")
                            print(f"  - 协议版本: {response.get('result', {}).get('protocolVersion')}")
                            print(f" - 服务器名称: {response.get('result', {}).get('serverInfo', {}).get('name')}")
                            print(f" - 服务器版本: {response.get('result', {}).get('serverInfo', {}).get('version')}")
                            break
                    except json.JSONDecodeError:
                        continue
                else:
                    time.sleep(0.1)
            except queue.Empty:
                time.sleep(0.1)

        if not response:
            print("\n❌ 超时：未收到初始化响应")
            return False

        # 发送 initialized 通知
        print("\n发送 initialized 通知...")
        init_notify = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }

        notify_json = json.dumps(init_notify) + "\n"
        proc.stdin.write(notify_json.encode('utf-8'))
        proc.stdin.flush()

        # 测试工具列表
        print("\n获取工具列表...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        tools_json = json.dumps(tools_request) + "\n"
        proc.stdin.write(tools_json.encode('utf-8'))
        proc.stdin.flush()

        # 等待工具列表响应
        response = None
        start_time = time.time()

        while time.time() - start_time < response_timeout:
            try:
                if not output_queue.empty():
                    line = output_queue.get(timeout=1)
                    response = json.loads(line)
                    if response.get("id") == 2:
                        tools = response.get("result", {}).get("tools", [])
                        print(f"\n✓ 成功获取工具列表! 共 {len(tools)} 个工具:")
                        for i, tool in enumerate(tools):
                            print(f"  {i+1}. {tool.get('name')}: {tool.get('description', '')[:50]}...")
                        break
            except queue.Empty:
                time.sleep(0.1)

        if not response:
            print("\n❌ 超时：未收到工具列表响应")
            return False

        print("\n=== MCP 服务器测试成功! ===")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理
        try:
            if 'proc' in locals():
                proc.terminate()
                proc.wait(timeout=5)
        except:
            pass

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)