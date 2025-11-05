#!/usr/bin/env python3
"""
调试版 MCP 服务器 - 输出详细信息
"""
import json
import sys
import os
import traceback

def debug_log(message):
    """输出调试信息到 stderr"""
    sys.stderr.write(f"[DEBUG] {message}\n")
    sys.stderr.flush()

class DebugMCPServer:
    """调试版 MCP 服务器"""

    def __init__(self):
        self.initialized = False
        debug_log("服务器初始化")

    def handle_request(self, request):
        """处理请求"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            debug_log(f"收到请求: method={method}, id={request_id}")

            if method == "initialize":
                self.initialized = True
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {
                                "listChanged": True
                            }
                        },
                        "serverInfo": {
                            "name": "douyin-mcp-server1",
                            "version": "1.2.2"
                        }
                    }
                }
                debug_log(f"初始化响应: {response}")
                return response

            elif method and method.startswith("notifications/"):
                debug_log(f"收到通知: {method}")
                return None

            elif method == "tools/list":
                debug_log("返回工具列表")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [
                            {
                                "name": "get_douyin_download_link",
                                "description": "获取抖音视频的无水印下载链接",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "share_link": {
                                            "type": "string",
                                            "description": "抖音分享链接"
                                        }
                                    },
                                    "required": ["share_link"]
                                }
                            },
                            {
                                "name": "parse_douyin_video_info",
                                "description": "解析抖音视频基本信息",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "share_link": {
                                            "type": "string",
                                            "description": "抖音分享链接"
                                        }
                                    },
                                    "required": ["share_link"]
                                }
                            }
                        ]
                    }
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                debug_log(f"调用工具: {tool_name}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"工具 {tool_name} 调用成功"
                            }
                        ]
                    }
                }

            else:
                debug_log(f"未知请求: {method}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"未知方法: {method}"
                    }
                }

        except Exception as e:
            debug_log(f"处理请求出错: {e}\n{traceback.format_exc()}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }


def main():
    """主函数"""
    debug_log("MCP 服务器启动")
    debug_log(f"Python 路径: {sys.executable}")
    debug_log(f"工作目录: {os.getcwd()}")
    debug_log(f"环境变量: DASHSCOPE_API_KEY={'SET' if os.getenv('DASHSCOPE_API_KEY') else 'NOT SET'}")

    server = DebugMCPServer()

    try:
        # 主循环
        debug_log("开始监听输入...")
        line_count = 0

        while True:
            try:
                line = sys.stdin.readline()
                line_count += 1

                if not line:
                    debug_log("EOF，退出")
                    break

                line = line.strip()
                if not line:
                    continue

                debug_log(f"收到第 {line_count} 行: {line[:100]}...")

                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    debug_log(f"JSON 解析错误: {e}")
                    continue

                # 处理请求
                response = server.handle_request(request)

                # 输出响应（通知不需要响应）
                if response is not None:
                    response_json = json.dumps(response, ensure_ascii=False)
                    debug_log(f"发送响应: {response_json[:200]}...")
                    sys.stdout.write(response_json + "\n")
                    sys.stdout.flush()
                else:
                    debug_log("通知，不发送响应")

            except KeyboardInterrupt:
                debug_log("键盘中断")
                break
            except Exception as e:
                debug_log(f"处理循环错误: {e}\n{traceback.format_exc()}")
                continue

    except Exception as e:
        debug_log(f"服务器启动失败: {e}\n{traceback.format_exc()}")
        sys.exit(1)

    debug_log("服务器退出")


if __name__ == "__main__":
    main()