#!/usr/bin/env python3
"""
调试 MCP 连接问题
"""

import json
import sys
import os

def test_server():
    """测试服务器启动"""
    print("=== 调试 MCP 服务器启动问题 ===", file=sys.stderr)

    # 测试1：简单初始化
    print("\n1. 测试简单初始化...", file=sys.stderr)
    try:
        # 读取初始化请求
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}}
            }
        }

        # 直接调用处理函数
        sys.path.insert(0, '.')
        from douyin_mcp_server1.server import handle_request

        response = handle_request(init_request)
        print("✅ 初始化成功", file=sys.stderr)
        print(f"响应: {json.dumps(response, ensure_ascii=False)}")

    except Exception as e:
        print(f"❌ 初始化失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False

    # 测试2：工具列表
    print("\n2. 测试工具列表...", file=sys.stderr)
    try:
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        response = handle_request(tools_request)
        tools = response.get("result", {}).get("tools", [])
        print(f"✅ 工具数量: {len(tools)}", file=sys.stderr)
        for tool in tools:
            print(f"  - {tool['name']}")

    except Exception as e:
        print(f"❌ 工具列表失败: {e}", file=sys.stderr)
        return False

    # 测试3：完整流程
    print("\n3. 测试完整流程...", file=sys.stderr)
    try:
        # 模拟真实的 stdin 输入
        import subprocess

        process = subprocess.Popen(
            [sys.executable, "-m", "douyin_mcp_server1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy()
        )

        # 发送初始化
        init_json = json.dumps(init_request) + "\n"
        stdout, stderr = process.communicate(init_json, timeout=5)

        print(f"退出码: {process.returncode}", file=sys.stderr)
        if stdout:
            print(f"输出: {stdout}", file=sys.stderr)
        if stderr:
            print(f"错误: {stderr}", file=sys.stderr)

        return process.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ 超时", file=sys.stderr)
        process.kill()
        return False
    except Exception as e:
        print(f"❌ 进程错误: {e}", file=sys.stderr)
        return False

    return True

if __name__ == "__main__":
    success = test_server()
    sys.exit(0 if success else 1)