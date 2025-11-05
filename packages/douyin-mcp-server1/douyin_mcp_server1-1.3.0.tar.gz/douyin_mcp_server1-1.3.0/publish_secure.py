#!/usr/bin/env python3
"""
安全的发布脚本 - 不在代码中存储敏感信息
"""
import os
import subprocess
import sys
import getpass

def main():
    print("=" * 60)
    print("抖音 MCP 服务器 - 安全发布脚本")
    print("=" * 60)
    print("\n⚠️  本脚本不会存储您的 API 密钥\n")

    # 获取 PyPI Token
    token = getpass.getpass("请输入您的 PyPI API Token (输入时不显示): ")

    if not token:
        print("❌ 未提供 API Token")
        sys.exit(1)

    # 确认
    print(f"\n准备发布 douyin-mcp-server1")
    response = input("\n确认继续？(y/N): ")
    if response.lower() != 'y':
        print("发布已取消")
        return

    # 清理
    print("\n🧹 清理旧文件...")
    subprocess.run(["rm", "-rf", "dist/", "build/", "*.egg-info/"], shell=False)

    # 构建依赖
    print("\n📦 安装构建工具...")
    subprocess.run([sys.executable, "-m", "pip", "install", "build", "twine"], check=True)

    # 构建
    print("\n🔨 构建包...")
    subprocess.run([sys.executable, "-m", "build"], check=True)

    # 检查
    print("\n🔍 检查包...")
    result = subprocess.run([sys.executable, "-m", "twine", "check", "dist/*"], capture_output=True)
    if result.returncode != 0:
        print("❌ 包检查失败:")
        print(result.stderr)
        sys.exit(1)

    # 发布
    print("\n🚀 发布到 PyPI...")
    env = os.environ.copy()
    env["TWINE_USERNAME"] = "__token__"
    env["TWINE_PASSWORD"] = token

    result = subprocess.run(
        [sys.executable, "-m", "twine", "upload", "dist/*"],
        env=env
    )

    if result.returncode == 0:
        print("\n🎉 发布成功！")
        print("\n安装命令:")
        print("  pip install douyin-mcp-server1")
        print("  uvx install douyin-mcp-server1")
    else:
        print("\n❌ 发布失败")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n发布已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
    finally:
        # 确保清理敏感信息
        if 'token' in locals():
            del token