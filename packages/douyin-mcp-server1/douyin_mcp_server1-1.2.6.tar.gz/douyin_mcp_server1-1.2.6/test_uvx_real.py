#!/usr/bin/env python3
"""
真实模拟 uvx 执行
"""
import subprocess
import json
import sys
import os

def test_real_uvx():
    print("=== 真实模拟 uvx 执行 ===\n")

    # 1. 测试脚本入口点（uvx实际使用的方式）
    print("1. 测试脚本入口点...")
    try:
        # 模拟 uvx 创建的脚本
        result = subprocess.run(
            [sys.executable, "-c", "from douyin_mcp_server1.mcp_server_simple import main; main()"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n',
            timeout=5
        )

        print(f"返回码: {result.returncode}")
        if result.stdout:
            print(f"stdout: {result.stdout[:200]}...")
        if result.stderr:
            print(f"stderr: {result.stderr[:200]}...")

        if result.returncode == 0 and "result" in result.stdout:
            print("✅ 脚本入口点成功")
        else:
            print("❌ 脚本入口点失败")

    except subprocess.TimeoutExpired:
        print("❌ 超时")
    except Exception as e:
        print(f"❌ 错误: {e}")

    # 2. 测试命令行工具方式
    print("\n2. 测试命令行工具...")
    try:
        # 检查脚本是否存在
        script_path = os.path.join(os.path.dirname(__file__), "douyin_mcp_server1", "mcp_server_simple.py")
        print(f"脚本路径: {script_path}")

        # 直接执行 Python 模块
        proc = subprocess.Popen(
            [sys.executable, "-m", "douyin_mcp_server1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 发送数据
        proc.stdin.write('{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n')
        proc.stdin.flush()

        # 读取响应
        try:
            stdout, stderr = proc.communicate(timeout=3)
            print(f"返回码: {proc.returncode}")
            if stdout:
                print(f"stdout: {stdout[:200]}...")
            if stderr:
                print(f"stderr: {stderr[:200]}...")

            if proc.returncode == 0 and "result" in stdout:
                print("✅ 命令行工具成功")
            else:
                print("❌ 命令行工具失败")
        except subprocess.TimeoutExpired:
            print("❌ 超时")
            proc.kill()

    except Exception as e:
        print(f"❌ 错误: {e}")

    # 3. 测试环境变量和依赖
    print("\n3. 测试环境...")
    try:
        # 测试导入
        import_result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, '.'); "
             "from douyin_mcp_server1.mcp_server_simple import SimpleMCPServer; "
             "print('Import successful')"],
            capture_output=True,
            text=True
        )

        if import_result.returncode == 0:
            print("✅ 导入测试成功")
        else:
            print(f"❌ 导入失败: {import_result.stderr}")

    except Exception as e:
        print(f"❌ 错误: {e}")

    # 4. 执行一个完整的MCP流程
    print("\n4. 完整MCP流程测试...")
    try:
        # 启动服务器
        proc = subprocess.Popen(
            [sys.executable, "-c", "from douyin_mcp_server1.mcp_server_simple import main; main()"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "DASHSCOPE_API_KEY": "test_key"}
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

        # 发送并获取响应
        stdout, stderr = proc.communicate(
            input=json.dumps(init_msg) + "\n",
            timeout=5
        )

        print(f"返回码: {proc.returncode}")

        # 检查响应
        if stdout:
            try:
                response = json.loads(stdout.strip())
                if "result" in response and "serverInfo" in response["result"]:
                    server_info = response["result"]["serverInfo"]
                    print(f"✅ 服务器响应正常")
                    print(f"   名称: {server_info['name']}")
                    print(f"   版本: {server_info['version']}")
                else:
                    print(f"❌ 响应格式错误: {response}")
            except json.JSONDecodeError:
                print(f"❌ JSON解析失败: {stdout[:100]}...")

        if stderr:
            # 检查是否有严重错误
            if "Error" in stderr or "error" in stderr:
                print(f"❌ 有错误输出: {stderr[:200]}...")
            else:
                print("   (stderr有调试信息，这是正常的)")

    except subprocess.TimeoutExpired:
        print("❌ 执行超时")
        if 'proc' in locals():
            proc.kill()
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_real_uvx()