#!/usr/bin/env python3
"""
测试 MCP 服务器启动
"""
import subprocess
import json
import sys
import time

def test_mcp_server():
    """测试 MCP 服务器初始化"""
    print("测试 MCP 服务器启动...")

    # 测试初始化消息
    init_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }

    # 启动服务器进程
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "douyin_mcp_server1.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )

        # 发送初始化消息
        init_json = json.dumps(init_message) + "\n"
        proc.stdin.write(init_json)
        proc.stdin.flush()

        # 读取响应（设置超时）
        start_time = time.time()
        timeout = 10  # 10秒超时

        response_line = ""
        while time.time() - start_time < timeout:
            if proc.poll() is not None:
                # 进程已退出
                stderr_output = proc.stderr.read()
                print(f"服务器进程退出，返回码: {proc.returncode}")
                if stderr_output:
                    print(f"错误输出: {stderr_output}")
                return False

            line = proc.stdout.readline()
            if line:
                response_line = line.strip()
                break
            time.sleep(0.1)
        else:
            # 超时
            print("响应超时")
            proc.terminate()
            return False

        # 解析响应
        if response_line:
            try:
                response = json.loads(response_line)
                if "result" in response:
                    print("✅ MCP 服务器初始化成功！")
                    print(f"服务器信息: {response.get('result', {}).get('serverInfo', {})}")

                    # 发送 initialized 通知
                    initialized_message = {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized"
                    }
                    initialized_json = json.dumps(initialized_message) + "\n"
                    proc.stdin.write(initialized_json)
                    proc.stdin.flush()

                    # 关闭服务器
                    proc.terminate()
                    return True
                elif "error" in response:
                    print(f"❌ 服务器返回错误: {response['error']}")
                    proc.terminate()
                    return False
            except json.JSONDecodeError as e:
                print(f"❌ 解析响应失败: {e}")
                print(f"原始响应: {response_line}")
                proc.terminate()
                return False

        return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_direct_import():
    """测试直接导入"""
    print("\n测试直接导入...")
    try:
        from douyin_mcp_server1.server import mcp, main
        print("✅ 导入成功")

        # 检查工具是否注册
        tools = mcp.list_tools()
        print(f"✅ 注册的工具数量: {len(tools)}")
        for tool in tools[:3]:  # 显示前3个工具
            print(f"   - {tool.get('name', 'unknown')}")

        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("MCP 服务器测试")
    print("=" * 60)

    # 测试导入
    import_ok = test_direct_import()

    # 测试服务器启动
    if import_ok:
        server_ok = test_mcp_server()
    else:
        server_ok = False

    print("\n" + "=" * 60)
    if import_ok and server_ok:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
        sys.exit(1)