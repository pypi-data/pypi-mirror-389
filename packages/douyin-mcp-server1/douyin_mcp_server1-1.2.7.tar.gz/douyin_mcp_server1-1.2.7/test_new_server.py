#!/usr/bin/env python3
"""
测试新的 MCP 服务器
"""
import subprocess
import json
import sys

def test_server():
    """测试服务器启动和初始化"""
    print("测试新的 MCP 服务器...")

    # 启动服务器
    proc = subprocess.Popen(
        [sys.executable, "-m", "douyin_mcp_server1.mcp_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 发送初始化消息
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
        # 发送消息
        proc.stdin.write(json.dumps(init_msg) + "\n")
        proc.stdin.flush()

        # 读取响应
        response = proc.stdout.readline()
        if response:
            resp_data = json.loads(response.strip())
            if "result" in resp_data:
                print("✅ 初始化成功!")
                print(f"服务器名称: {resp_data['result']['serverInfo']['name']}")

                # 发送工具列表请求
                tools_msg = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list"
                }

                proc.stdin.write(json.dumps(tools_msg) + "\n")
                proc.stdin.flush()

                # 读取工具列表
                tools_response = proc.stdout.readline()
                if tools_response:
                    tools_data = json.loads(tools_response.strip())
                    tools = tools_data.get("result", {}).get("tools", [])
                    print(f"✅ 工具数量: {len(tools)}")
                    for tool in tools:
                        print(f"   - {tool['name']}")

                proc.terminate()
                return True
            else:
                print(f"❌ 初始化失败: {resp_data}")
                return False
        else:
            print("❌ 没有响应")
            stderr = proc.stderr.read()
            if stderr:
                print(f"错误: {stderr}")
            proc.terminate()
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        proc.terminate()
        return False

def main():
    print("=" * 60)
    print("测试 douyin-mcp-server1 v1.2.1")
    print("=" * 60)

    # 测试导入
    try:
        import sys
        sys.path.insert(0, '.')
        from douyin_mcp_server1.mcp_server import main, MCPServer
        print("✅ 导入成功")
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        print("\n提示: 需要安装依赖:")
        print("pip install ffmpeg-python dashscope")
        return

    # 测试服务器
    if test_server():
        print("\n✅ 所有测试通过!")
        print("\n更新版本并发布:")
        print("1. rm -rf dist/ build/")
        print("2. python -m build")
        print("3. python -m twine upload dist/*")
        print("\n使用 uvx 安装:")
        print("uvx install douyin-mcp-server1==1.2.1")
    else:
        print("\n❌ 测试失败")

if __name__ == "__main__":
    main()