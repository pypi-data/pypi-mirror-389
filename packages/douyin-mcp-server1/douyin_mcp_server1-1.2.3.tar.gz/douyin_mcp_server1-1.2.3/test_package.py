#!/usr/bin/env python3
"""
测试包是否可以正常安装和运行
"""
import subprocess
import sys
import tempfile
import os

def run_command(cmd, capture=True):
    """运行命令"""
    print(f"运行: {' '.join(cmd)}")
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    else:
        result = subprocess.run(cmd)
        return result.returncode == 0, "", ""

def test_install():
    """测试安装"""
    print("\n=== 测试本地安装 ===")

    # 创建临时环境
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = os.path.join(tmpdir, "test_venv")

        # 创建虚拟环境
        success, _, _ = run_command([sys.executable, "-m", "venv", venv_path])
        if not success:
            print("❌ 创建虚拟环境失败")
            return False

        # 虚拟环境路径
        if os.name == "nt":
            python_path = os.path.join(venv_path, "Scripts", "python.exe")
            pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
        else:
            python_path = os.path.join(venv_path, "bin", "python")
            pip_path = os.path.join(venv_path, "bin", "pip")

        # 安装包
        print("安装包...")
        success, out, err = run_command([pip_path, "install", "-e", "."])
        if not success:
            print(f"❌ 安装失败: {err}")
            return False

        # 测试导入
        print("测试导入...")
        success, out, err = run_command([
            python_path, "-c",
            "from douyin_mcp_server1 import DouyinProcessor; print('✅ 导入成功')"
        ])
        if not success:
            print(f"❌ 导入失败: {err}")
            return False

        print("✅ 本地安装测试通过")
        return True

def test_uvx():
    """测试 uvx"""
    print("\n=== 测试 uvx ===")

    # 检查 uvx
    success, _, _ = run_command(["uvx", "--version"], capture=False)
    if not success:
        print("⚠️  uvx 未安装，跳过测试")
        return True

    print("✅ uvx 可用")
    return True

def main():
    """主测试"""
    print("=" * 60)
    print("douyin-mcp-server1 包测试")
    print("=" * 60)

    all_passed = True

    # 测试本地安装
    if not test_install():
        all_passed = False

    # 测试 uvx
    if not test_uvx():
        all_passed = False

    # 结果
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
        print("\n准备发布命令:")
        print("  ./build_and_publish.sh")
    else:
        print("❌ 部分测试失败，请修复后重试")
        sys.exit(1)

if __name__ == "__main__":
    main()