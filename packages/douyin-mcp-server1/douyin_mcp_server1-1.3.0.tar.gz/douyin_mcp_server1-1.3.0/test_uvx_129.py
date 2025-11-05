#!/usr/bin/env python3
"""测试 uvx 部署 1.2.9 版本"""
import subprocess
import json
import time

print("=== 测试 uvx 部署 1.2.9 版本 ===\n")

# 1. 先测试是否能获取到包
print("1. 检查 PyPI 上的版本...")
try:
    result = subprocess.run(
        ["uv", "--index-url", "https://pypi.org/simple", "pip", "show", "douyin-mcp-server1"],
        capture_output=True,
        text=True,
        timeout=10
    )
    print(f"返回码: {result.returncode}")
    if result.stdout:
        print(f"输出: {result.stdout[:500]}")
    if result.stderr:
        print(f"错误: {result.stderr[:500]}")
except Exception as e:
    print(f"异常: {e}")

print("\n" + "="*50 + "\n")

# 2. 测试 uvx 安装并运行
print("2. 测试 uvx 运行 1.2.9...")
try:
    # 使用 timeout 防止卡住
    process = subprocess.run(
        ["uvx", "--index-url", "https://pypi.org/simple", "douyin-mcp-server1==1.2.9"],
        input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}}}}\n',
        capture_output=True,
        text=True,
        timeout=10
    )

    print(f"返回码: {process.returncode}")
    if process.stdout:
        print(f"输出: {process.stdout}")
    if process.stderr:
        print(f"错误: {process.stderr}")

    # 解析输出
    if process.stdout:
        try:
            response = json.loads(process.stdout.strip())
            if "result" in response:
                version = response["result"]["serverInfo"]["version"]
                print(f"\n✅ 成功！版本: {version}")
        except:
            pass

except subprocess.TimeoutExpired:
    print("❌ 超时：可能等待输入或卡住了")
except Exception as e:
    print(f"❌ 异常: {e}")

print("\n" + "="*50 + "\n")

# 3. 测试本地 wheel 文件
print("3. 测试本地 wheel 文件...")
import os
wheel_path = "/app/test/douyin-mcp-server/dist/douyin_mcp_server1-1.2.9-py3-none-any.whl"
if os.path.exists(wheel_path):
    try:
        process2 = subprocess.run(
            ["uvx", wheel_path],
            input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}}}}\n',
            capture_output=True,
            text=True,
            timeout=10
        )

        print(f"返回码: {process2.returncode}")
        if process2.stdout:
            print(f"输出: {process2.stdout}")
        if process2.stderr:
            print(f"错误: {process2.stderr}")

    except subprocess.TimeoutExpired:
        print("❌ 超时")
    except Exception as e:
        print(f"❌ 异常: {e}")
else:
    print("❌ Wheel 文件不存在")

print("\n" + "="*50 + "\n")

# 4. 直接运行 python 测试
print("4. 直接运行 Python 测试...")
try:
    process3 = subprocess.run(
        ["python3", "-m", "douyin_mcp_server1.mcp_server_simple"],
        input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}}}}\n',
        capture_output=True,
        text=True,
        timeout=5,
        cwd="/app/test/douyin-mcp-server"
    )

    print(f"返回码: {process3.returncode}")
    if process3.stdout:
        print(f"输出: {process3.stdout}")
    if process3.stderr:
        print(f"错误: {process3.stderr}")

except Exception as e:
    print(f"❌ 异常: {e}")