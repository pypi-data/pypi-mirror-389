#!/usr/bin/env python3
"""
最终解决方案
"""
import subprocess
import json
import sys

def final_solution():
    print("="*60)
    print("douyin-mcp-server1 部署最终解决方案")
    print("="*60)

    # 解决方案1：强制使用官方PyPI
    print("\n方案1：强制使用官方PyPI")
    print("""
配置：
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["--default-index", "https://pypi.org/simple", "douyin-mcp-server1==1.2.5"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
    """)

    # 解决方案2：使用pipx风格
    print("\n方案2：如果方案1不行，尝试pipx安装")
    print("""
# 先手动安装
pipx install douyin-mcp-server1==1.2.5 --index-url https://pypi.org/simple

# 然后配置使用已安装的版本
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "pipx",
      "args": ["run", "douyin-mcp-server1==1.2.5"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
    """)

    # 解决方案3：本地Python环境
    print("\n方案3：使用本地Python环境")
    print("""
# 安装到用户环境
pip install --user --index-url https://pypi.org/simple douyin-mcp-server1==1.2.5

# 配置
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "python",
      "args": ["-m", "douyin_mcp_server1"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
    """)

    # 测试当前环境
    print("\n测试当前环境...")

    # 测试直接使用官方源
    cmd = ["uvx", "--default-index", "https://pypi.org/simple", "douyin-mcp-server1==1.2.5", "--help"]
    print(f"\n测试命令: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ 命令执行成功，包可用！")
        else:
            print(f"❌ 命令失败: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print("❌ 超时")
    except Exception as e:
        print(f"❌ 错误: {e}")

    print("\n" + "="*60)
    print("关键要点：")
    print("1. 使用 --default-index https://pypi.org/simple 强制使用官方源")
    print("2. 确保DASHSCOPE_API_KEY在env中，不是args中")
    print("3. 版本1.2.5已经在PyPI官方源上可用")
    print("\n如果还是不行，请检查：")
    print("- 网络是否能访问 https://pypi.org")
    print("- uvx版本是否太旧")
    print("- 是否有防火墙限制")

if __name__ == "__main__":
    final_solution()