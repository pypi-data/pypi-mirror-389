#!/usr/bin/env python3
"""
深入调试 uvx 问题
"""
import subprocess
import json
import sys
import time
import os

def debug_uvx():
    print("=== 深入调试 uvx 问题 ===\n")

    # 1. 检查 uvx 版本和环境
    print("1. 检查 uvx 环境...")
    try:
        result = subprocess.run(["uvx", "--version"], capture_output=True, text=True)
        print(f"uvx 版本: {result.stdout.strip()}")

        # 检查 uv 缓存
        result = subprocess.run(["uvx", "--help"], capture_output=True, text=True)
        if "--index-url" in result.stdout:
            print("✅ uvx 支持 --index-url")
    except:
        print("❌ uvx 不可用")

    # 2. 尝试使用官方 PyPI 源
    print("\n2. 测试官方 PyPI 源...")
    try:
        cmd = [
            "uvx",
            "--index-url", "https://pypi.org/simple",
            "douyin-mcp-server1==1.2.5"
        ]
        print(f"命令: {' '.join(cmd)}")

        env = os.environ.copy()
        env["DASHSCOPE_API_KEY"] = "test_key"

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
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }

        try:
            stdout, stderr = proc.communicate(
                input=json.dumps(init_msg) + "\n",
                timeout=15
            )

            print(f"返回码: {proc.returncode}")
            if stdout:
                print(f"stdout: {stdout[:200]}...")
            if stderr:
                print(f"stderr: {stderr[:400]}...")

            if proc.returncode == 0 and "result" in stdout:
                print("✅ 使用官方源成功！")
            else:
                print("❌ 使用官方源失败")

        except subprocess.TimeoutExpired:
            print("❌ 超时")
            proc.kill()

    except Exception as e:
        print(f"❌ 错误: {e}")

    # 3. 尝试不使用 uvx，直接模拟 uvx 的行为
    print("\n3. 模拟 uvx 行为...")
    try:
        # 创建临时目录
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        venv_dir = os.path.join(temp_dir, "test_venv")

        print(f"创建虚拟环境: {venv_dir}")

        # 创建虚拟环境
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)

        # 获取 python 路径
        if os.name == "nt":
            python_path = os.path.join(venv_dir, "Scripts", "python.exe")
            pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:
            python_path = os.path.join(venv_dir, "bin", "python")
            pip_path = os.path.join(venv_dir, "bin", "pip")

        # 升级 pip
        subprocess.run([pip_path, "install", "--upgrade", "pip"], capture_output=True)

        # 安装包（使用官方源）
        print("安装包...")
        install_result = subprocess.run(
            [pip_path, "install", "-i", "https://pypi.org/simple", "douyin-mcp-server1==1.2.5"],
            capture_output=True,
            text=True
        )

        if install_result.returncode == 0:
            print("✅ 安装成功")
        else:
            print(f"❌ 安装失败: {install_result.stderr}")
            # 尝试 1.2.4
            print("尝试安装 1.2.4...")
            install_result = subprocess.run(
                [pip_path, "install", "-i", "https://pypi.org/simple", "douyin-mcp-server1==1.2.4"],
                capture_output=True,
                text=True
            )
            if install_result.returncode == 0:
                print("✅ 1.2.4 安装成功")
            else:
                print(f"❌ 1.2.4 安装也失败: {install_result.stderr}")

        # 测试运行
        print("测试运行...")
        env = os.environ.copy()
        env["DASHSCOPE_API_KEY"] = "test_key"
        env["VIRTUAL_ENV"] = venv_dir
        env["PATH"] = os.path.join(venv_dir, "bin") + ":" + env.get("PATH", "")

        run_result = subprocess.run(
            [python_path, "-m", "douyin_mcp_server1"],
            input=json.dumps(init_msg) + "\n",
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )

        print(f"运行返回码: {run_result.returncode}")
        if run_result.stdout:
            print(f"运行输出: {run_result.stdout[:200]}...")
        if run_result.stderr:
            print(f"运行错误: {run_result.stderr[:200]}...")

        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        print(f"❌ 模拟错误: {e}")

    # 4. 检查网络连接
    print("\n4. 检查网络连接...")
    try:
        import urllib.request
        response = urllib.request.urlopen("https://pypi.org/pypi/douyin-mcp-server1/json", timeout=5)
        data = json.loads(response.read().decode())
        versions = list(data["releases"].keys())
        print(f"PyPI上的版本: {sorted(versions)[-5:]}")
    except Exception as e:
        print(f"❌ 无法访问PyPI: {e}")

    print("\n" + "="*60)
    print("总结：")
    print("1. 如果 uvx 无法找到包，可能是镜像问题")
    print("2. 使用 --index-url https://pypi.org/simple 强制使用官方源")
    print("3. 或考虑本地安装方式")
    print("\n建议的配置：")
    print("""
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["--index-url", "https://pypi.org/simple", "douyin-mcp-server1==1.2.4"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
    """)

if __name__ == "__main__":
    debug_uvx()