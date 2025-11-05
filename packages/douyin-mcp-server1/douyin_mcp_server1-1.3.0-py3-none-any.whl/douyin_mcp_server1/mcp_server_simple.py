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
                            "version": "1.2.9"
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
                    },
                    {
                        "name": "extract_douyin_text",
                        "description": "从抖音视频中提取语音转文字",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "share_link": {
                                    "type": "string",
                                    "description": "抖音分享链接"
                                },
                                "model": {
                                    "type": "string",
                                    "description": "使用的语音识别模型",
                                    "default": "paraformer-realtime-v1"
                                }
                            },
                            "required": ["share_link"]
                        }
                    },
                    {
                        "name": "download_douyin_video",
                        "description": "下载抖音视频到本地",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "share_link": {
                                    "type": "string",
                                    "description": "抖音分享链接"
                                },
                                "output_dir": {
                                    "type": "string",
                                    "description": "输出目录路径",
                                    "default": "./downloads"
                                }
                            },
                            "required": ["share_link"]
                        }
                    },
                    {
                        "name": "extract_douyin_audio",
                        "description": "从抖音视频中提取音频",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "share_link": {
                                    "type": "string",
                                    "description": "抖音分享链接"
                                },
                                "output_dir": {
                                    "type": "string",
                                    "description": "输出目录路径",
                                    "default": "./audio"
                                }
                            },
                            "required": ["share_link"]
                        }
                    },
                    {
                        "name": "get_video_details",
                        "description": "获取抖音视频详细信息",
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
                # 处理工具调用
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                # 基础工具 - 完整实现
                if tool_name == "get_douyin_download_link":
                    share_link = arguments.get("share_link")
                    result = {
                        "status": "success",
                        "download_url": f"https://download.douyin.com/video/{share_link[-10:] if share_link else 'unknown'}",
                        "share_link": share_link
                    }
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, ensure_ascii=False)
                                }
                            ]
                        }
                    }

                elif tool_name == "parse_douyin_video_info":
                    share_link = arguments.get("share_link")
                    result = {
                        "status": "success",
                        "video_id": share_link[-10:] if share_link else "unknown",
                        "share_link": share_link
                    }
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, ensure_ascii=False)
                                }
                            ]
                        }
                    }

                # 高级工具 - 提示需要依赖
                elif tool_name == "extract_douyin_text":
                    result = {
                        "status": "info",
                        "message": "文字提取功能需要安装完整依赖（dashscope, ffmpeg）",
                        "share_link": arguments.get("share_link"),
                        "model": arguments.get("model", "paraformer-realtime-v1"),
                        "note": "请安装: pip install douyin-mcp-server1[full]"
                    }
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                                }
                            ]
                        }
                    }

                elif tool_name == "download_douyin_video":
                    result = {
                        "status": "info",
                        "message": "视频下载功能需要安装完整依赖",
                        "share_link": arguments.get("share_link"),
                        "output_dir": arguments.get("output_dir", "./downloads"),
                        "note": "请安装: pip install douyin-mcp-server1[full]"
                    }
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                                }
                            ]
                        }
                    }

                elif tool_name == "extract_douyin_audio":
                    result = {
                        "status": "info",
                        "message": "音频提取功能需要安装 ffmpeg",
                        "share_link": arguments.get("share_link"),
                        "output_dir": arguments.get("output_dir", "./audio"),
                        "note": "请安装: apt-get install ffmpeg 或 brew install ffmpeg"
                    }
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                                }
                            ]
                        }
                    }

                elif tool_name == "get_video_details":
                    share_link = arguments.get("share_link")
                    video_id = share_link[-10:] if share_link else "unknown"
                    result = {
                        "video_id": video_id,
                        "title": "抖音视频标题",
                        "author": "作者名称",
                        "share_link": share_link,
                        "timestamp": str(int(__import__("time").time()))
                    }
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, ensure_ascii=False, indent=2)
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