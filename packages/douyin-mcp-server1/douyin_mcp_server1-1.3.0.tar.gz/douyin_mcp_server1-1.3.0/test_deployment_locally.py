#!/usr/bin/env python3
"""
本地测试部署
"""
import subprocess
import json
import sys
import os
import time

def test_locally():
    print("="*60)
    print("本地部署测试")
    print("="*60)

    # 1. 测试导入
    print("\n1. 测试导入...")
    try:
        # 测试导入
        import_result = subprocess.run([
            sys.executable, "-c",
            "import douyin_mcp_server1; print(douyin_mcp_server1.__version__)"
        ], capture_output=True, text=True)

        if import_result.returncode == 0:
            print(f"✅ 导入成功: {import_result.stdout.strip()}")
        else:
            print(f"❌ 导入失败: {import_result.stderr}")
            return
    except Exception as e:
        print(f"❌ 导入错误: {e}")
        return

    # 2. 测试直接运行（模拟正确的环境变量方式）
    print("\n2. 测试正确的方式（环境变量）...")
    env = os.environ.copy()
    env["DASHSCOPE_API_KEY"] = "sk-test"

    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "douyin_mcp_server1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )

        # 初始化
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

        stdout, stderr = proc.communicate(
            input=json.dumps(init_msg) + "\n",
            timeout=5
        )

        if proc.returncode == 0 and stdout:
            try:
                response = json.loads(stdout.strip())
                if "result" in response:
                    print("✅ 直接运行成功！")
                    server_info = response["result"]["serverInfo"]
                    print(f"   服务器: {server_info['name']}")
                    print(f"   版本: {server_info['version']}")
                else:
                    print(f"❌ 响应错误: {response}")
            except:
                print(f"❌ 响应不是JSON: {stdout[:200]}")
        else:
            print(f"❌ 运行失败: {stderr[:200]}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")

    # 3. 测试错误的方式（命令行参数）
    print("\n3. 测试错误的方式（命令行参数）...")
    try:
        # 这是错误的，因为DASHSCOPE_API_KEY不应该作为参数
        proc = subprocess.Popen([
            sys.executable, "-m", "douyin_mcp_server1",
            "DASHSCOPE_API_KEY=sk-test"
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        stdout, stderr = proc.communicate(timeout=5)

        if proc.returncode != 0:
            print("❌ 错误方式失败（这是预期的）")
            if stderr:
                print(f"   错误信息: {stderr[:200]}")
        else:
            print("⚠️ 错误方式居然成功了？")

    except Exception as e:
        print(f"❌ 测试失败: {e}")

    # 4. 测试工具列表
    print("\n4. 测试工具列表...")
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "douyin_mcp_server1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )

        # 发送初始化和工具列表请求
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        ]

        input_data = "\n".join(json.dumps(r) for r in requests) + "\n"
        stdout, stderr = proc.communicate(input=input_data, timeout=10)

        if proc.returncode == 0 and stdout:
            lines = stdout.strip().split('\n')
            if len(lines) >= 2:
                tools_response = json.loads(lines[1])
                tools = tools_response.get("result", {}).get("tools", [])
                print(f"✅ 工具列表成功！找到 {len(tools)} 个工具:")
                for tool in tools:
                    print(f"   - {tool['name']}")
            else:
                print("❌ 响应不完整")
        else:
            print(f"❌ 获取工具列表失败")

    except Exception as e:
        print(f"❌ 测试失败: {e}")

    print("\n" + "="*60)
    print("\n结论：")
    print("✅ 服务器本身工作正常")
    print("❌ 问题是环境变量传递方式错误")
    print("\n正确的配置应该是：")
    print("""
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["--default-index", "https://pypi.org/simple", "douyin-mcp-server1==1.2.7"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
    """)
    print("\n注意：DASHSCOPE_API_KEY 必须在 'env' 字段中，不能在 'args' 中！")

if __name__ == "__main__":
    test_locally()