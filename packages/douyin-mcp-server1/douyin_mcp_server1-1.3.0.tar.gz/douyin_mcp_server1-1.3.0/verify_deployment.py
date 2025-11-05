#!/usr/bin/env python3
"""
验证部署 - 使用正确的方式测试MCP服务器
"""
import subprocess
import json
import sys
import time

def verify():
    print("=" * 60)
    print("douyin-mcp-server1 部署验证")
    print("=" * 60)

    # 测试1: 直接模块执行（uvx使用的方式）
    print("\n1. 测试模块执行...")
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "douyin_mcp_server1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={"DASHSCOPE_API_KEY": "test_key"}
        )

        # 发送初始化请求
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

        # 使用communicate发送数据并接收响应
        stdout, stderr = proc.communicate(
            input=json.dumps(init_request) + "\n",
            timeout=5
        )

        # 检查结果
        if proc.returncode == 0 and stdout:
            response = json.loads(stdout.strip())
            if "result" in response:
                server_info = response["result"]["serverInfo"]
                print(f"✅ 初始化成功")
                print(f"   服务器: {server_info['name']}")
                print(f"   版本: {server_info['version']}")
            else:
                print(f"❌ 响应错误: {response}")
        else:
            print(f"❌ 执行失败: {stderr}")

    except Exception as e:
        print(f"❌ 错误: {e}")

    # 测试2: 测试工具列表
    print("\n2. 测试工具列表...")
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "douyin_mcp_server1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={"DASHSCOPE_API_KEY": "test_key"}
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

        # 发送工具列表请求
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        # 组合请求
        input_data = json.dumps(init_request) + "\n" + json.dumps(tools_request) + "\n"

        stdout, stderr = proc.communicate(input=input_data, timeout=5)

        if proc.returncode == 0 and stdout:
            lines = stdout.strip().split('\n')
            if len(lines) >= 2:
                init_response = json.loads(lines[0])
                tools_response = json.loads(lines[1])

                if "result" in init_response and "result" in tools_response:
                    tools = tools_response["result"].get("tools", [])
                    print(f"✅ 获取工具列表成功")
                    print(f"   工具数量: {len(tools)}")
                    for tool in tools:
                        print(f"   - {tool['name']}: {tool['description']}")
                else:
                    print("❌ 响应格式错误")
            else:
                print("❌ 响应不完整")
        else:
            print(f"❌ 执行失败")

    except Exception as e:
        print(f"❌ 错误: {e}")

    print("\n" + "=" * 60)
    print("✅ 验证完成！")
    print("\n部署说明:")
    print("1. PyPI包已发布: https://pypi.org/project/douyin-mcp-server1/1.2.5/")
    print("2. 使用命令: uvx douyin-mcp-server1==1.2.5")
    print("3. 或安装到环境: pip install douyin-mcp-server1==1.2.5")
    print("\n功能:")
    print("- get_douyin_download_link: 获取抖音无水印下载链接")
    print("- parse_douyin_video_info: 解析抖音视频信息")
    print("\n注意:")
    print("- 需要设置 DASHSCOPE_API_KEY 环境变量")
    print("- 音频处理功能需要安装 ffmpeg")

if __name__ == "__main__":
    verify()