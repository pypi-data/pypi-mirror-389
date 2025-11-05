#!/usr/bin/env python3
"""
完整的 uvx 部署测试
"""
import subprocess
import json
import sys
import os

def test_uvx_deployment():
    print("="*60)
    print("UVX 部署完整测试")
    print("="*60)

    # 获取当前目录的wheel文件
    wheel_path = os.path.join(os.path.dirname(__file__), "dist", "douyin_mcp_server1-1.2.5-py3-none-any.whl")

    print(f"\n1. 测试本地wheel文件安装...")
    print(f"Wheel路径: {wheel_path}")

    # 测试1: 使用本地wheel文件
    try:
        cmd = ["uvx", wheel_path]
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

        stdout, stderr = proc.communicate(
            input=json.dumps(init_msg) + "\n",
            timeout=15
        )

        print(f"返回码: {proc.returncode}")
        if stdout:
            print(f"输出: {stdout[:200]}...")
        if stderr:
            print(f"错误: {stderr[:300]}...")

        if proc.returncode == 0 and "result" in stdout:
            print("✅ 本地wheel文件测试成功！")
            return True
        else:
            print("❌ 本地wheel文件测试失败")

    except subprocess.TimeoutExpired:
        print("❌ 超时")
        proc.kill()
    except Exception as e:
        print(f"❌ 错误: {e}")

    # 测试2: 尝试不同版本的PyPI镜像
    mirrors = [
        ("官方", "https://pypi.org/simple"),
        ("华为云", "https://mirrors.huaweicloud.com/repository/pypi/simple/"),
        ("阿里云", "https://mirrors.aliyun.com/pypi/simple/"),
        ("豆瓣", "https://pypi.douban.com/simple/"),
    ]

    print("\n2. 测试不同PyPI镜像...")

    for name, url in mirrors:
        print(f"\n测试 {name} 镜像: {url}")

        try:
            # 先检查包是否存在
            check_cmd = ["uvx", "--default-index", url, "douyin-mcp-server1==1.2.4", "--help"]
            result = subprocess.run(
                check_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print(f"✅ {name} 镜像可用！")

                # 测试完整功能
                cmd = ["uvx", "--default-index", url, "douyin-mcp-server1==1.2.4"]
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

                stdout, stderr = proc.communicate(
                    input=json.dumps(init_msg) + "\n",
                    timeout=15
                )

                if proc.returncode == 0 and "result" in stdout:
                    print(f"✅ {name} 镜像完整测试成功！")
                    print(f"\n✅✅✅ 找到可用镜像：{name}")
                    print(f"✅✅✅ 使用命令：uvx --default-index {url} douyin-mcp-server1==1.2.4")
                    return True
            else:
                print(f"❌ {name} 镜像不可用")

        except subprocess.TimeoutExpired:
            print(f"❌ {name} 镜像超时")
        except Exception as e:
            print(f"❌ {name} 镜像错误: {e}")

    # 测试3: 使用HTTP链接
    print("\n3. 测试直接HTTP链接...")

    # 检查是否可以从PyPI下载
    import urllib.request
    try:
        wheel_url = "https://files.pythonhosted.org/packages/5f/f9/douyin_mcp_server1-1.2.5-py3-none-any.whl"
        # 这个URL是示例，实际需要从PyPI获取
        print("检查包的下载URL...")
        response = urllib.request.urlopen(f"https://pypi.org/pypi/douyin-mcp-server1/1.2.5/json", timeout=5)
        data = json.loads(response.read().decode())

        # 查找wheel URL
        for file_info in data.get("urls", []):
            if file_info["packagetype"] == "bdist_wheel" and file_info["python_version"] == "py3":
                wheel_url = file_info["url"]
                print(f"找到wheel URL: {wheel_url}")

                # 测试直接从URL安装
                cmd = ["uvx", wheel_url]
                print(f"\n测试命令: {' '.join(cmd)}")

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

                stdout, stderr = proc.communicate(
                    input=json.dumps(init_msg) + "\n",
                    timeout=20
                )

                if proc.returncode == 0 and "result" in stdout:
                    print("✅ 直接URL安装成功！")
                    return True
                else:
                    print(f"❌ 直接URL安装失败: {stderr[:200]}...")
                break

    except Exception as e:
        print(f"❌ 无法获取下载URL: {e}")

    print("\n" + "="*60)
    print("✅✅✅ 最终建议 ✅✅✅")
    print("\n如果上述测试中有成功的方案，使用相应的配置：")
    print("""
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["--default-index", "成功的镜像URL", "douyin-mcp-server1==1.2.4"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
    """)

    print("\n或使用本地文件方式：")
    print(f"""
1. 下载wheel文件到本地
2. 使用配置：
{{
  "mcpServers": {{
    "douyin-mcp1": {{
      "command": "uvx",
      "args": ["{wheel_path}"],
      "env": {{
        "DASHSCOPE_API_KEY": "你的API密钥"
      }}
    }}
  }}
}}
    """)

    return False

if __name__ == "__main__":
    test_uvx_deployment()