#!/usr/bin/env python3
"""
测试MCP集成 - 模拟MCP代理的调用方式
"""
import subprocess
import json
import sys
import os

def test_mcp_integration():
    print("=== 测试MCP集成 ===")

    # 1. 错误的方式（当前日志中的方式）
    print("\n1. 测试错误的方式（当前的方式）...")
    try:
        # 这是当前日志中的错误方式
        cmd = ["uvx", "douyin-mcp-server1==1.2.5", "DASHSCOPE_API_KEY=sk-27ed62f0217240a38efcebff00eeee42"]
        print(f"命令: {' '.join(cmd)}")

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 发送初始化
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-proxy", "version": "1.0"}
            }
        }

        stdout, stderr = proc.communicate(
            input=json.dumps(init_msg) + "\n",
            timeout=10
        )

        print(f"返回码: {proc.returncode}")
        if stderr:
            print(f"stderr: {stderr[:300]}...")
        if stdout:
            print(f"stdout: {stdout[:200]}...")

        if proc.returncode != 0:
            print("❌ 失败：这是错误的方式")
        else:
            print("✅ 意外成功")

    except Exception as e:
        print(f"❌ 错误: {e}")

    # 2. 正确的方式（使用环境变量）
    print("\n2. 测试正确的方式...")
    try:
        # 设置环境变量
        env = os.environ.copy()
        env["DASHSCOPE_API_KEY"] = "sk-27ed62f0217240a38efcebff00eeee42"

        # 正确的命令
        cmd = ["uvx", "douyin-mcp-server1==1.2.5"]
        print(f"命令: {' '.join(cmd)}")
        print(f"环境变量: DASHSCOPE_API_KEY=...")

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )

        # 发送初始化
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-proxy", "version": "1.0"}
            }
        }

        stdout, stderr = proc.communicate(
            input=json.dumps(init_msg) + "\n",
            timeout=10
        )

        print(f"返回码: {proc.returncode}")
        if stdout:
            try:
                response = json.loads(stdout.strip())
                if "result" in response:
                    server_info = response["result"]["serverInfo"]
                    print(f"✅ 成功！")
                    print(f"   服务器: {server_info['name']}")
                    print(f"   版本: {server_info['version']}")
                else:
                    print(f"❌ 响应错误: {response}")
            except:
                print(f"❌ 响应不是有效JSON: {stdout[:200]}...")

        if stderr:
            if "ERROR" in stderr or "Error" in stderr:
                print(f"❌ 错误输出: {stderr[:300]}...")
            else:
                print(f"   (调试信息: {stderr[:100]}...)")

    except Exception as e:
        print(f"❌ 错误: {e}")

    # 3. 测试直接调用（不使用uvx）
    print("\n3. 测试直接调用（绕过uvx）...")
    try:
        # 使用本地安装的版本
        cmd = [sys.executable, "-m", "douyin_mcp_server1"]
        print(f"命令: {' '.join(cmd)}")

        env = os.environ.copy()
        env["DASHSCOPE_API_KEY"] = "sk-27ed62f0217240a38efcebff00eeee42"

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )

        # 发送完整的初始化流程
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-proxy", "version": "1.0"}
            }
        }

        stdout, stderr = proc.communicate(
            input=json.dumps(init_msg) + "\n",
            timeout=10
        )

        print(f"返回码: {proc.returncode}")
        if stdout:
            response = json.loads(stdout.strip())
            if "result" in response:
                print("✅ 直接调用成功！")

    except Exception as e:
        print(f"❌ 错误: {e}")

    print("\n" + "="*60)
    print("结论和建议：")
    print("1. uvx命令行参数传递方式错误")
    print("2. 环境变量应该在env配置中传递，而不是作为args")
    print("\n正确的配置应该是：")
    print("""
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["douyin-mcp-server1==1.2.5"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
    """)

if __name__ == "__main__":
    test_mcp_integration()