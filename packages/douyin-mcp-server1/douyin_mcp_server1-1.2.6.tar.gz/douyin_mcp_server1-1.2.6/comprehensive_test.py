#!/usr/bin/env python3
"""
全面的部署测试
"""
import subprocess
import json
import sys
import time
import os
import tempfile
import threading
import queue
import signal

def test_local_import():
    """测试本地导入"""
    print("\n=== 测试1: 本地导入 ===")
    try:
        sys.path.insert(0, '.')
        from douyin_mcp_server1.mcp_server_simple import SimpleMCPServer as MCPServer
        print("✅ 导入成功")
        server = MCPServer()
        print("✅ 实例化成功")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_module_execution():
    """测试模块执行"""
    print("\n=== 测试2: 模块执行 ===")
    try:
        # 启动服务器进程
        proc = subprocess.Popen(
            [sys.executable, "-m", "douyin_mcp_server1.mcp_server_simple"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "DASHSCOPE_API_KEY": "test_key"}
        )

        # 发送初始化
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

        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        # 读取响应
        response = proc.stdout.readline()
        if response:
            data = json.loads(response.strip())
            if "result" in data:
                print("✅ 模块执行成功")
                proc.terminate()
                return True

        # 读取错误
        stderr = proc.stderr.read()
        if stderr:
            print(f"错误: {stderr}")

        proc.terminate()
        return False

    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_wheel_installation():
    """测试 wheel 安装"""
    print("\n=== 测试3: Wheel 安装测试 ===")
    try:
        # 创建临时虚拟环境
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        venv_dir = os.path.join(temp_dir, "test_venv")

        # 创建虚拟环境
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)

        # 获取 python 路径
        if os.name == "nt":
            python_path = os.path.join(venv_dir, "Scripts", "python.exe")
            pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:
            python_path = os.path.join(venv_dir, "bin", "python")
            pip_path = os.path.join(venv_dir, "bin", "pip")

        # 安装包
        wheel_path = "/app/test/douyin-mcp-server/dist/douyin_mcp_server1-1.2.4-py3-none-any.whl"
        result = subprocess.run([pip_path, "install", wheel_path], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ 安装失败: {result.stderr}")
            shutil.rmtree(temp_dir)
            return False

        print("✅ Wheel 安装成功")

        # 测试脚本执行
        result = subprocess.run([python_path, "-c", "from douyin_mcp_server1 import main; main()"],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                input=json.dumps({
                                    "jsonrpc": "2.0",
                                    "id": 1,
                                    "method": "initialize",
                                    "params": {
                                        "protocolVersion": "2024-11-05",
                                        "capabilities": {},
                                        "clientInfo": {"name": "test", "version": "1.0"}
                                    }
                                }) + "\n",
                                text=True,
                                timeout=5)

        # 清理
        shutil.rmtree(temp_dir)

        if "result" in result.stdout:
            print("✅ 虚拟环境执行成功")
            return True
        else:
            print(f"❌ 执行失败: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_full_mcp_flow():
    """测试完整的 MCP 流程"""
    print("\n=== 测试4: 完整 MCP 流程 ===")
    try:
        # 启动服务器
        proc = subprocess.Popen(
            [sys.executable, "-m", "douyin_mcp_server1.mcp_server_simple"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={"DASHSCOPE_API_KEY": "test_key"}
        )

        # 1. 初始化
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

        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        response = proc.stdout.readline()
        data = json.loads(response.strip())
        if "error" in data:
            print(f"❌ 初始化失败: {data}")
            proc.terminate()
            return False
        print("✅ 初始化成功")

        # 2. 发送 initialized 通知
        init_notify = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        proc.stdin.write(json.dumps(init_notify) + "\n")
        proc.stdin.flush()

        # 3. 获取工具列表
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        proc.stdin.write(json.dumps(tools_request) + "\n")
        proc.stdin.flush()

        response = proc.stdout.readline()
        data = json.loads(response.strip())
        tools = data.get("result", {}).get("tools", [])
        print(f"✅ 获取到 {len(tools)} 个工具")

        # 4. 调用工具
        if tools:
            tool_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tools[0]["name"],
                    "arguments": {"share_link": "test"}
                }
            }

            proc.stdin.write(json.dumps(tool_request) + "\n")
            proc.stdin.flush()

            response = proc.stdout.readline()
            data = json.loads(response.strip())
            if "result" in data:
                print(f"✅ 工具调用成功: {tools[0]['name']}")
            else:
                print(f"❌ 工具调用失败: {data}")

        proc.terminate()
        return True

    except Exception as e:
        print(f"❌ 失败: {e}")
        if 'proc' in locals():
            proc.terminate()
        return False

def test_entry_point():
    """测试入口点脚本"""
    print("\n=== 测试5: 入口点脚本 ===")
    try:
        # 模拟安装后执行
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, '.'); import douyin_mcp_server1; douyin_mcp_server1.main()"],
            input=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"}
                }
            }) + "\n",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )

        if "result" in result.stdout:
            print("✅ 入口点脚本执行成功")
            return True
        else:
            print(f"❌ 失败: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("douyin-mcp-server1 v1.2.3 部署测试")
    print("=" * 60)

    tests = [
        ("本地导入", test_local_import),
        ("模块执行", test_module_execution),
        ("Wheel安装", test_wheel_installation),
        ("完整MCP流程", test_full_mcp_flow),
        ("入口点脚本", test_entry_point)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n开始测试: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} 通过")
        else:
            print(f"❌ {test_name} 失败")

    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！包已准备好用于生产部署。")
        print("\n使用方法:")
        print("uvx install douyin-mcp-server1==1.2.3")
        return True
    else:
        print("\n❌ 部分测试失败，需要修复问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)