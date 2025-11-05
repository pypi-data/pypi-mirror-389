#!/usr/bin/env python3
"""
测试简化版 MCP 服务器
"""
import subprocess
import json
import sys

def test_simple_server():
    """测试简化版服务器"""
    print("测试简化版 MCP 服务器...")

    # 启动服务器
    proc = subprocess.Popen(
        [sys.executable, "-m", "douyin_mcp_server1.mcp_server_simple"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 发送初始化请求
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
        # 发送请求
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        # 读取响应
        response_line = proc.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            if "result" in response:
                print("✅ 初始化成功!")
                print(f"服务器: {response['result']['serverInfo']['name']}")

                # 发送 initialized 通知
                init_notify = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }
                proc.stdin.write(json.dumps(init_notify) + "\n")
                proc.stdin.flush()

                # 测试工具列表
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list"
                }
                proc.stdin.write(json.dumps(tools_request) + "\n")
                proc.stdin.flush()

                tools_response = proc.stdout.readline()
                if tools_response:
                    tools_data = json.loads(tools_response.strip())
                    tools = tools_data.get("result", {}).get("tools", [])
                    print(f"✅ 工具列表: {len(tools)} 个工具")

                proc.terminate()
                return True
            else:
                print(f"❌ 初始化失败: {response}")
                # 读取错误输出
                stderr = proc.stderr.read()
                if stderr:
                    print(f"错误: {stderr}")
                return False
        else:
            print("❌ 没有响应")
            stderr = proc.stderr.read()
            if stderr:
                print(f"错误: {stderr}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        proc.terminate()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("测试简化版 MCP 服务器")
    print("=" * 60)

    if test_simple_server():
        print("\n✅ 测试通过!")
    else:
        print("\n❌ 测试失败")