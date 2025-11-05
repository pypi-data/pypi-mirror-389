#!/usr/bin/env python3
"""
简化的 MCP 服务器入口点 - 不依赖外部库
"""
import json
import sys
import os
import traceback


class SimpleMCPServer:
    """最简化的 MCP 服务器实现"""

    def __init__(self):
        self.initialized = False

    def handle_request(self, request):
        """处理请求"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "initialize":
                self.initialized = True
                return {
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
                            "version": "1.2.5"
                        }
                    }
                }

            # 通知不需要响应
            elif method and method.startswith("notifications/"):
                # 不返回任何响应
                return None

            elif method == "tools/list":
                tools = [
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

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": tools
                    }
                }

            elif method == "tools/call":
                # 简单实现，只返回测试响应
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                if tool_name == "get_douyin_download_link":
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": '{"status": "success", "message": "下载链接功能测试成功"}'
                                }
                            ]
                        }
                    }
                elif tool_name == "parse_douyin_video_info":
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": '{"status": "success", "message": "视频信息解析功能测试成功"}'
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"未知工具: {tool_name}"
                        }
                    }

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"未知方法: {method}"
                    }
                }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }


def main():
    """主函数 - 同步处理"""
    server = SimpleMCPServer()

    # 调试信息
    sys.stderr.write("MCP Server Starting...\n")
    sys.stderr.flush()

    try:
        # 读取输入并响应
        for line in sys.stdin:
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                # 解析请求
                request = json.loads(line)

                # 处理请求
                response = server.handle_request(request)

                # 输出响应（通知不需要响应）
                if response is not None:
                    response_json = json.dumps(response, ensure_ascii=False)
                    sys.stdout.write(response_json + "\n")
                    sys.stdout.flush()

            except json.JSONDecodeError:
                continue
            except Exception as e:
                sys.stderr.write(f"Error: {e}\n")
                sys.stderr.flush()

    except Exception as e:
        sys.stderr.write(f"Fatal error: {e}\n")
        sys.stderr.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()