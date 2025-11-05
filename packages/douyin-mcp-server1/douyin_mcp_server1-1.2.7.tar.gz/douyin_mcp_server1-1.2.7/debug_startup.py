#!/usr/bin/env python3
"""
调试 uvx 启动问题
"""
import subprocess
import json
import sys
import os
import tempfile

def debug_startup():
    """调试启动问题"""
    print("=== 调试 uvx 启动 ===")

    # 1. 检查 uvx 是否可用
    print("\n1. 检查 uvx...")
    try:
        result = subprocess.run(["which", "uvx"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uvx 路径: {result.stdout.strip()}")
        else:
            print("❌ uvx 未找到")
            return
    except:
        print("❌ 无法检查 uvx")
        return

    # 2. 创建临时目录来测试
    print("\n2. 创建测试环境...")
    with tempfile.TemporaryDirectory() as temp_dir:
        # 3. 创建测试脚本
        test_script = """
import sys
import json
import os

print("=== 脚本启动 ===")
print(f"Python: {sys.executable}")
print(f"Args: {sys.argv}")
print(f"CWD: {os.getcwd()}")

# 设置环境变量
os.environ['DASHSCOPE_API_KEY'] = 'test_key'

# 尝试导入
try:
    import douyin_mcp_server1
    print("✅ 导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 尝试获取 main 函数
try:
    main = douyin_mcp_server1.main
    print("✅ 获取 main 成功")
except Exception as e:
    print(f"❌ 获取 main 失败: {e}")
    sys.exit(1)

print("✅ 准备就绪，开始监听 stdin...")

# 监听 stdin 并响应
try:
    for line in sys.stdin:
        if not line:
            break
        line = line.strip()
        if not line:
            continue

        print(f"收到: {line}")

        try:
            request = json.loads(line)
            method = request.get("method")

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "test", "version": "1.0"}
                    }
                }
                print(f"响应: {json.dumps(response)}")
                sys.stdout.write(json.dumps(response))
                sys.stdout.write("\n")
                sys.stdout.flush()
        except:
            pass

except KeyboardInterrupt:
    print("退出")
"""

        test_file = os.path.join(temp_dir, "test_server.py")
        with open(test_file, 'w') as f:
            f.write(test_script)

        # 4. 测试直接运行
        print("\n3. 测试直接运行...")
        proc = subprocess.Popen(
            [sys.executable, test_file],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
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

        print(f"\n发送请求: {json.dumps(init_request)}")
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        # 等待响应
        import select
        if select.select([proc.stdout], [], [], 3):
            response = proc.stdout.readline()
            if response:
                print(f"收到响应: {response.strip()}")
                try:
                    data = json.loads(response.strip())
                    if "result" in data:
                        print("✅ 测试成功！")
                        return True
                except:
                    pass

        # 读取错误
        _, stderr = proc.communicate(timeout=1)
        if stderr:
            print(f"错误输出:\n{stderr}")

    print("\n=== 测试结束 ===")
    return False


if __name__ == "__main__":
    debug_startup()