#!/usr/bin/env python3
"""
调试 uvx 启动问题
"""
import subprocess
import sys

def test_uvx_command():
    """测试 uvx 命令"""
    print("测试 uvx 命令...")

    # 测试 uvx 版本
    try:
        result = subprocess.run(["uvx", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uvx 版本: {result.stdout.strip()}")
        else:
            print("❌ uvx 未正确安装")
            return False
    except FileNotFoundError:
        print("❌ uvx 未找到")
        print("请安装 uvx: pip install uvx")
        return False

    # 测试包是否可以安装
    print("\n测试包安装...")
    cmd = ["uvx", "--verbose", "douyin-mcp-server1", "--help"]
    print(f"执行命令: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"\n返回码: {result.returncode}")
        if result.stdout:
            print(f"\n标准输出:\n{result.stdout}")
        if result.stderr:
            print(f"\n标准错误:\n{result.stderr}")

    except subprocess.TimeoutExpired:
        print("❌ 命令超时")
        return False
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        return False

    return True

def test_direct_run():
    """测试直接运行"""
    print("\n测试直接运行 Python 模块...")

    # 首先安装依赖（模拟）
    print("\n提示: 需要先安装 ffmpeg-python")
    print("pip install ffmpeg-python")

    # 测试模块导入
    test_cmd = """
import sys
sys.path.insert(0, '/app/test/douyin-mcp-server')

try:
    from douyin_mcp_server1.server import mcp
    print("✅ 模块导入成功")
    print(f"工具数量: {len(mcp.tools) if hasattr(mcp, 'tools') else '未知'}")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("提示: 需要安装 ffmpeg-python")
"""

    result = subprocess.run([sys.executable, "-c", test_cmd], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"错误: {result.stderr}")

def create_requirements():
    """创建 requirements.txt"""
    with open("requirements.txt", "w") as f:
        f.write("""# MCP 服务器依赖
mcp>=1.0.0
fastmcp
requests
ffmpeg-python
tqdm
dashscope
""")
    print("\n✅ 创建 requirements.txt")

def main():
    print("=" * 60)
    print("调试 uvx 启动问题")
    print("=" * 60)

    # 创建 requirements
    create_requirements()

    # 测试
    test_uvx_command()
    test_direct_run()

    print("\n" + "=" * 60)
    print("解决方案建议:")
    print("1. 确保安装了所有依赖: pip install ffmpeg-python")
    print("2. 使用 pip 安装: pip install douyin-mcp-server1")
    print("3. 手动运行: python -m douyin_mcp_server1")
    print("4. 检查 MCP 客户端配置中的命令参数")
    print("=" * 60)

if __name__ == "__main__":
    main()