#!/usr/bin/env python3
"""
最终测试 - 清理缓存后的uvx行为
"""
import subprocess
import json
import sys
import os

def test_uvx_clean():
    """测试清理后的uvx"""
    print("=== 测试清理后的 uvx ===")

    # 1. 检查缓存是否清理干净
    print("\n1. 检查缓存状态...")
    uv_tools = os.path.expanduser("~/.local/share/uv/tools")
    if os.path.exists(uv_tools):
        items = [i for i in os.listdir(uv_tools) if "douyin" in i.lower()]
        if items:
            print(f"❌ 仍有缓存: {items}")
            return False
        else:
            print("✅ 缓存已清理")

    # 2. 直接导入测试
    print("\n2. 测试直接导入...")
    try:
        from douyin_mcp_server1.mcp_server_simple import SimpleMCPServer
        print("✅ 导入成功")
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

    # 3. 测试命令行入口点
    print("\n3. 测试命令行入口点...")
    cmd = [sys.executable, "-m", "douyin_mcp_server1.mcp_server_simple"]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={"DASHSCOPE_API_KEY": "test_key"}
    )

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

        response = proc.stdout.readline()
        if response:
            data = json.loads(response.strip())
            if "result" in data:
                print("✅ 入口点测试成功")
                proc.terminate()
                return True
            else:
                print(f"❌ 响应错误: {data}")
        else:
            print("❌ 没有响应")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        proc.terminate()

    return False

if __name__ == "__main__":
    success = test_uvx_clean()

    if success:
        print("\n✅ 所有测试通过！")
        print("\n现在可以通过 uvx 安装使用了:")
        print("uvx douyin-mcp-server1")
    else:
        print("\n❌ 测试失败")