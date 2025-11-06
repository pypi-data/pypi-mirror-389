#!/usr/bin/env python3
"""
MCP 服务器诊断工具
"""

import json
import sys
import subprocess
import time

def run_command(cmd, description="", timeout=10):
    """运行命令并显示输出"""
    print(f"\n{'='*60}")
    print(f"运行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            print(f"✓ 成功")
            if result.stdout:
                print(f"输出:\n{result.stdout[:500]}")
        else:
            print(f"❌ 失败 (退出码: {result.returncode})")
            if result.stderr:
                print(f"错误:\n{result.stderr[:500]}")

        return result.returncode == 0, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        print(f"❌ 超时 (> {timeout}秒)")
        return False, "", "命令超时"
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False, "", str(e)

def diagnose_mcp_server():
    print("\n🔍 MCP 服务器诊断工具\n")

    # 1. 检查 Python 环境
    print("\n1️⃣ 检查 Python 环境...")
    run_command([sys.executable, "--version"], "Python 版本")
    run_command([sys.executable, "-c", "import sys; print(f'Python路径: {sys.executable}')"], "Python 路径")

    # 2. 检查 uvx
    print("\n2️⃣ 检查 uvx...")
    run_command(["uvx", "--version"], "uvx 版本")

    # 3. 测试本地安装
    print("\n3️⃣ 测试本地安装...")
    run_command([sys.executable, "-m", "pip", "show", "douyin-mcp-server1"], "检查本地安装")

    # 4. 测试导入
    print("\n4️⃣ 测试导入...")
    run_command([sys.executable, "-c", "import douyin_mcp_server1; print('导入成功')"], "测试导入")

    # 5. 测试直接运行
    print("\n5️⃣ 测试直接运行...")

    # 创建测试输入
    test_input = [
        '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}',
        '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
    ]

    cmd = [sys.executable, "-m", "douyin_mcp_server1"]
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        print(f"  启动命令: {' '.join(cmd)}")

        # 发送测试输入
        for i, test in enumerate(test_input):
            print(f"\n  发送测试 {i+1}: {test[:50]}...")
            process.stdin.write(test + "\n")
            process.stdin.flush()

            # 读取响应
            start_time = time.time()
            while time.time() - start_time < 5:
                if process.poll() is not None:
                    break
                time.sleep(0.1)

            if process.poll() is not None:
                print(f"  ⚠️  进程已退出")
                break

    except Exception as e:
        print(f"  ❌ 运行错误: {e}")

    finally:
        if 'process' in locals() and process.poll() is None:
            process.terminate()

    # 6. 测试 uvx 安装和运行
    print("\n6️⃣ 测试 uvx 安装...")

    # 先检查是否在镜像上
    print("\n  检查 PyPI 官方源...")
    run_command(
        ["curl", "-s", "https://pypi.org/simple/douyin-mcp-server1/"],
        "检查 PyPI 官方源",
        timeout=5
    )

    print("\n  检查 Aliyun 镜像...")
    run_command(
        ["curl", "-s", "https://mirrors.aliyun.com/pypi/simple/douyin-mcp-server1/"],
        "检查 Aliyun 镜像",
        timeout=5
    )

    # 7. 提供解决方案
    print(f"\n{'='*60}")
    print("💡 解决方案")
    print(f"{'='*60}")

    print("\n1️⃣ 立即可用的解决方案:")
    print("   - 使用本地安装:")
    print("     pip install douyin-mcp-server1==1.5.0")
    print("     douyin-mcp-server1")

    print("\n2️⃣ 对于 uvx 部署，可能需要等待镜像同步（1-6小时）")
    print("   - 使用 1.4.5 版本（已在镜像上）")

    print("\n3️⃣ 如果仍然失败，检查:")
    print("   - 网络连接")
    print("   - Python 环境 (>=3.10)")
    print("   - 权限设置")
    print("   - 防火墙配置")

if __name__ == "__main__":
    diagnose_mcp_server()