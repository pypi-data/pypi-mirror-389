#!/usr/bin/env python3
"""
发布脚本 - 用于发布 douyin-mcp-server1 到 PyPI
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """运行命令并处理结果"""
    print(f"\n{'='*60}")
    print(f"执行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print('='*60)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ 成功: {description}")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ 失败: {description}")
        if result.stderr:
            print(f"错误信息:\n{result.stderr}")
        sys.exit(1)

    return result

def main():
    """主发布流程"""
    print("="*60)
    print("抖音 MCP 服务器 - 发布脚本 v1")
    print("="*60)

    # 检查当前目录
    if not Path("pyproject.toml").exists():
        print("❌ 错误: 请在项目根目录运行此脚本")
        sys.exit(1)

    # 确认发布
    print("\n⚠️  即将发布 douyin-mcp-server1")
    response = input("\n确认继续？(y/N): ")
    if response.lower() != 'y':
        print("发布已取消")
        return

    # 清理旧的构建文件
    print("\n🧹 清理旧的构建文件...")
    if Path("dist").exists():
        import shutil
        shutil.rmtree("dist")
    if Path("build").exists():
        import shutil
        shutil.rmtree("build")

    # 更新版本号（可选）
    print("\n📝 检查版本信息...")
    import toml
    with open("pyproject.toml", "r") as f:
        config = toml.load(f)
    version = config["project"]["version"]
    print(f"当前版本: {version}")

    update_version = input("是否更新版本号？(y/N): ")
    if update_version.lower() == 'y':
        new_version = input("输入新版本号 (例如: 1.3.0): ")
        config["project"]["version"] = new_version
        with open("pyproject.toml", "w") as f:
            toml.dump(config, f)
        print(f"✅ 版本已更新到: {new_version}")

    # 安装构建依赖
    print("\n📦 安装构建依赖...")
    run_command([
        sys.executable, "-m", "pip", "install", "--upgrade",
        "build", "twine", "wheel", "setuptools"
    ], "安装构建工具")

    # 运行测试（如果有）
    if Path("test").exists() or Path("tests").exists():
        print("\n🧪 运行测试...")
        run_command([sys.executable, "-m", "pytest", "-v"], "运行测试")

    # 检查包
    print("\n🔍 检查包配置...")
    run_command([sys.executable, "-m", "build", "."], "构建包")
    run_command([sys.executable, "-m", "twine", "check", "dist/*"], "检查包")

    # 上传到测试 PyPI（可选）
    upload_test = input("\n是否先上传到测试 PyPI？(y/N): ")
    if upload_test.lower() == 'y':
        print("\n🚀 上传到测试 PyPI...")
        run_command([sys.executable, "-m", "twine", "upload", "--repository", "testpypi", "dist/*"],
                   "上传到测试 PyPI")
        print("✅ 已上传到测试 PyPI")
        print("测试安装命令:")
        print("pip install -i https://test.pypi.org/simple/ douyin-mcp-server1")

    # 上传到正式 PyPI
    print("\n🚀 准备上传到正式 PyPI...")
    response = input("⚠️  这将发布到 PyPI，确认继续？(y/N): ")
    if response.lower() == 'y':
        run_command([sys.executable, "-m", "twine", "upload", "dist/*"], "上传到 PyPI")
        print("\n🎉 发布成功！")
        print("\n安装命令:")
        print("pip install douyin-mcp-server1")
        print("\n或使用 uvx:")
        print("uvx install douyin-mcp-server1")
    else:
        print("\n发布已取消")

def create_uv_test():
    """创建 uvx 测试脚本"""
    test_script = """#!/bin/bash
# 测试 uvx 安装

echo "测试 uvx 安装 douyin-mcp-server1..."

# 清理缓存
uv cache clean

# 安装并测试
uvx --verbose douyin-mcp-server1 --help

echo ""
echo "✅ uvx 测试完成"
"""

    with open("test_uvx.sh", "w") as f:
        f.write(test_script)

    os.chmod("test_uvx.sh", 0o755)
    print("✅ 创建测试脚本: test_uvx.sh")

if __name__ == "__main__":
    try:
        main()
        create_uv_test()
    except KeyboardInterrupt:
        print("\n\n发布已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发布失败: {e}")
        sys.exit(1)