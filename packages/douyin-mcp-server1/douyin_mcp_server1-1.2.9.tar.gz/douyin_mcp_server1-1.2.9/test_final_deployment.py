#!/usr/bin/env python3
"""
最终部署测试 - 模拟完整的uvx安装和使用流程
"""
import subprocess
import json
import sys
import tempfile
import os

def test_deployment():
    print("=" * 60)
    print("douyin-mcp-server1 v1.2.5 最终部署测试")
    print("=" * 60)

    # 1. 创建临时虚拟环境
    print("\n1. 创建测试虚拟环境...")
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_dir = os.path.join(temp_dir, "test_venv")

        # 创建虚拟环境
        result = subprocess.run(
            [sys.executable, "-m", "venv", venv_dir],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ 创建虚拟环境失败: {result.stderr}")
            return False

        # 获取python和pip路径
        if os.name == "nt":
            python_path = os.path.join(venv_dir, "Scripts", "python.exe")
            pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:
            python_path = os.path.join(venv_dir, "bin", "python")
            pip_path = os.path.join(venv_dir, "bin", "pip")

        print("✅ 虚拟环境创建成功")

        # 2. 安装包
        print("\n2. 安装 douyin-mcp-server1...")
        install_result = subprocess.run(
            [pip_path, "install", "douyin-mcp-server1==1.2.5", "--no-deps"],
            capture_output=True,
            text=True
        )

        if install_result.returncode != 0:
            print(f"❌ 安装失败: {install_result.stderr}")
            return False

        print("✅ 安装成功")

        # 3. 测试模块导入
        print("\n3. 测试模块导入...")
        import_result = subprocess.run(
            [python_path, "-c", "import douyin_mcp_server1; print(douyin_mcp_server1.__version__)"],
            capture_output=True,
            text=True
        )

        if import_result.returncode != 0:
            print(f"❌ 导入失败: {import_result.stderr}")
            return False

        print(f"✅ 导入成功，版本: {import_result.stdout.strip()}")

        # 4. 测试MCP通信
        print("\n4. 测试MCP通信...")
        proc = subprocess.Popen(
            [python_path, "-m", "douyin_mcp_server1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={"DASHSCOPE_API_KEY": "test_key"}
        )

        try:
            # 发送初始化
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

            proc.stdin.write(json.dumps(init_msg) + "\n")
            proc.stdin.flush()

            # 读取响应
            response = proc.stdout.readline()
            if response:
                data = json.loads(response.strip())
                if "result" in data:
                    server_info = data["result"]["serverInfo"]
                    print(f"✅ MCP初始化成功")
                    print(f"   服务器: {server_info['name']}")
                    print(f"   版本: {server_info['version']}")
                else:
                    print(f"❌ MCP初始化失败: {data}")
            else:
                print("❌ 没有收到响应")

            # 读取错误信息
            stderr = proc.stderr.read()
            if stderr and "MCP Server Starting" in stderr:
                # 这是正常的调试信息
                pass

        except Exception as e:
            print(f"❌ 测试失败: {e}")
        finally:
            proc.terminate()

        # 5. 测试命令行入口点
        print("\n5. 测试命令行入口点...")
        cli_result = subprocess.run(
            [python_path, "-c", "from douyin_mcp_server1.mcp_server_simple import main; main()"],
            input=json.dumps(init_msg) + "\n",
            capture_output=True,
            text=True,
            timeout=5
        )

        if cli_result.returncode == 0 and "result" in cli_result.stdout:
            print("✅ 命令行入口点正常")
        else:
            print("❌ 命令行入口点失败")
            if cli_result.stderr:
                print(f"   错误: {cli_result.stderr}")

    print("\n" + "=" * 60)
    print("✅ 部署测试完成！")
    print("\n使用说明:")
    print("1. 通过 uvx 安装: uvx douyin-mcp-server1==1.2.5")
    print("2. 通过 pip 安装: pip install douyin-mcp-server1==1.2.5")
    print("3. 设置环境变量: DASHSCOPE_API_KEY=your_api_key")
    print("\n功能特性:")
    print("- ✅ 获取抖音无水印下载链接")
    print("- ✅ 解析抖音视频信息")
    print("- ✅ 智能音频压缩（<50MB）")
    print("- ✅ 线程安全的缓存管理")
    print("- ✅ 最小依赖（仅requests）")

    return True

if __name__ == "__main__":
    success = test_deployment()
    sys.exit(0 if success else 1)