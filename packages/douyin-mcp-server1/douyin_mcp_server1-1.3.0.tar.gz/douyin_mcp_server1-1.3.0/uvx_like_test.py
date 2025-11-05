#!/usr/bin/env python3
"""
模拟 uvx 行为的测试
"""
import subprocess
import json
import sys
import os
import tempfile

def test_uvx_behavior():
    """测试 uvx 行为"""
    print("=== 模拟 uvx 行为测试 ===")

    # 创建一个模拟 uvx 环境的脚本
    test_script = """
import sys
import os
import site

# 模拟 uvx 的包查找路径
sys.path.insert(0, '/app/test/douyin-mcp-server')

# 设置环境变量
os.environ['DASHSCOPE_API_KEY'] = 'test_key'

# 延迟一点，模拟包加载
import time
time.sleep(0.1)

# 导入并运行
try:
    from douyin_mcp_server1 import main
    main()
except ImportError as e:
    print(f"导入错误: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"运行错误: {e}", file=sys.stderr)
    sys.exit(1)
"""

    # 创建测试环境
    with tempfile.TemporaryDirectory() as temp_dir:
        script_file = os.path.join(temp_dir, "uvx_test.py")
        with open(script_file, 'w') as f:
            f.write(test_script)

        # 运行模拟 uvx
        cmd = [sys.executable, script_file]

        print(f"执行命令: {cmd[0]}")
        print(f"工作目录: {temp_dir}")

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=temp_dir
        )

        # 发送初始化
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }

        print("\n发送初始化请求...")
        proc.stdin.write(json.dumps(init_request))
        proc.stdin.write("\n")
        proc.stdin.flush()

        # 等待响应
        try:
            import select
            if select.select([proc.stdout], [], [], 3):
                response = proc.stdout.readline()
                if response:
                    print(f"收到响应: {response.strip()}")
                    try:
                        data = json.loads(response.strip())
                        if "result" in data:
                            print("✅ 模拟 uvx 成功！")
                            proc.terminate()
                            return True
                    except:
                        print("JSON 解析失败")
                else:
                    print("没有收到响应")
        except:
            pass

        # 读取错误信息
        try:
            _, stderr = proc.communicate(timeout=1)
            if stderr:
                print(f"错误输出:\n{stderr}")
        except:
            pass

    return False


def check_uvx_cache():
    """检查 uvx 缓存"""
    print("\n=== 检查 uvx 缓存 ===")

    # uvx 的缓存位置
    uv_cache = os.path.expanduser("~/.local/share/uv")
    if os.path.exists(uv_cache):
        print(f"uv 缓存目录: {uv_cache}")

        # 列出缓存的项目
        for item in os.listdir(uv_cache):
            if "douyin" in item.lower():
                print(f"  - {item}")
    else:
        print("uv 缓存目录不存在")

    # uvx 的工具目录
    uv_tools = os.path.expanduser("~/.local/share/uv/tools")
    if os.path.exists(uv_tools):
        print(f"\nuv 工具目录: {uv_tools}")
        for item in os.listdir(uv_tools):
            if "douyin" in item.lower():
                print(f"  - {item}")

    # uvx 下载缓存
    uv_cache_dir = os.path.expanduser("~/.cache/uv")
    if os.path.exists(uv_cache_dir):
        print(f"\nuv 下载缓存: {uv_cache_dir}")
        # 查找相关文件
        for root, dirs, files in os.walk(uv_cache_dir):
            for file in files:
                if "douyin" in file.lower() or "mcp" in file.lower():
                    rel_path = os.path.relpath(os.path.join(root, file), uv_cache_dir)
                    print(f"  - {rel_path}")


if __name__ == "__main__":
    # 先检查缓存
    check_uvx_cache()

    # 测试模拟 uvx 行为
    success = test_uvx_behavior()

    if success:
        print("\n✅ 测试通过！")
        print("\n建议：")
        print("1. 清理 uvx 缓存：rm -rf ~/.local/share/uv/tools/douyin*")
        print("2. 或者使用全新环境安装")
        print("3. 检查 uvx 版本：uvx --version")
    else:
        print("\n❌ 测试失败")

    # 如果需要，尝试清除缓存
    import shutil
    uv_tools = os.path.expanduser("~/.local/share/uv/tools")
    if os.path.exists(uv_tools):
        for item in os.listdir(uv_tools):
            if "douyin" in item.lower():
                item_path = os.path.join(uv_tools, item)
                print(f"\n清除缓存: {item_path}")
                shutil.rmtree(item_path, ignore_errors=True)