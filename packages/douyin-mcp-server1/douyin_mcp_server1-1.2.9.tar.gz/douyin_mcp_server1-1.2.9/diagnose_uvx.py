#!/usr/bin/env python3
"""
诊断 uvx 执行问题
"""
import subprocess
import sys
import json
import tempfile
import os

def diagnose():
    print("=== 诊断 uvx 执行问题 ===")

    # 1. 测试入口点函数
    print("\n1. 测试入口点函数...")
    try:
        # 导入main函数
        from douyin_mcp_server1.mcp_server_simple import main
        print("✅ 成功导入main函数")

        # 检查函数类型
        import inspect
        print(f"✅ main函数类型: {type(main)}")
        print(f"✅ main函数签名: {inspect.signature(main)}")

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()

    # 2. 测试模块执行
    print("\n2. 测试 python -m 执行...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "douyin_mcp_server1"],
            input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n',
            capture_output=True,
            text=True,
            timeout=5
        )

        print(f"返回码: {result.returncode}")
        if result.stdout:
            print(f"输出: {result.stdout}")
        if result.stderr:
            print(f"错误: {result.stderr}")

    except subprocess.TimeoutExpired:
        print("❌ 超时")
    except Exception as e:
        print(f"❌ 错误: {e}")

    # 3. 测试脚本执行
    print("\n3. 测试脚本执行...")
    try:
        # 查找安装后的脚本路径
        result = subprocess.run(
            [sys.executable, "-c", "import douyin_mcp_server1; print(douyin_mcp_server1.__file__)"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            module_path = result.stdout.strip()
            script_path = os.path.join(os.path.dirname(module_path), "mcp_server_simple.py")
            print(f"✅ 模块路径: {module_path}")
            print(f"✅ 脚本路径: {script_path}")

            # 直接执行脚本
            result2 = subprocess.run(
                [sys.executable, "-c", f"from douyin_mcp_server1.mcp_server_simple import main; main()"],
                input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n',
                capture_output=True,
                text=True,
                timeout=5
            )

            print(f"返回码: {result2.returncode}")
            if result2.stdout:
                print(f"输出: {result2.stdout}")
            if result2.stderr:
                print(f"错误: {result2.stderr}")
        else:
            print(f"❌ 无法找到模块: {result.stderr}")

    except Exception as e:
        print(f"❌ 错误: {e}")

    # 4. 测试实际的安装包
    print("\n4. 测试wheel包...")
    wheel_path = "/app/test/douyin-mcp-server/dist/douyin_mcp_server1-1.2.4-py3-none-any.whl"
    if os.path.exists(wheel_path):
        print(f"✅ 找到wheel包: {wheel_path}")

        # 临时安装测试
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建虚拟环境
            venv_dir = os.path.join(temp_dir, "test_venv")
            subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)

            # 获取python路径
            if os.name == "nt":
                python_path = os.path.join(venv_dir, "Scripts", "python.exe")
            else:
                python_path = os.path.join(venv_dir, "bin", "python")

            # 安装包
            install_result = subprocess.run(
                [python_path, "-m", "pip", "install", wheel_path, "--no-deps"],
                capture_output=True,
                text=True
            )

            if install_result.returncode == 0:
                print("✅ 安装成功")

                # 测试运行
                test_result = subprocess.run(
                    [python_path, "-m", "douyin_mcp_server1"],
                    input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n',
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                print(f"返回码: {test_result.returncode}")
                if test_result.stdout:
                    print(f"输出: {test_result.stdout[:200]}...")
                if test_result.stderr:
                    print(f"错误: {test_result.stderr}")
            else:
                print(f"❌ 安装失败: {install_result.stderr}")
    else:
        print(f"❌ 没有找到wheel包")

if __name__ == "__main__":
    diagnose()