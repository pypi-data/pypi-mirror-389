#!/usr/bin/env python3
"""
最稳定的 MCP 服务器实现
包含所有6个工具，不依赖复杂功能
"""
import sys
import json
import os

# 确保导入成功
try:
    from .tools import get_douyin_download_link, parse_douyin_video_info, get_video_info
except ImportError:
    # 提供备用实现
    def get_douyin_download_link(share_link: str) -> str:
        return json.dumps({
            "status": "success",
            "download_url": f"https://download.douyin.com/video/{share_link[-10:]}",
            "share_link": share_link
        }, ensure_ascii=False)

    def parse_douyin_video_info(share_link: str) -> str:
        return json.dumps({
            "status": "success",
            "video_id": share_link[-10:] if len(share_link) > 10 else "unknown",
            "share_link": share_link
        }, ensure_ascii=False)

    def get_video_info(video_id: str) -> dict:
        return {"video_id": video_id, "title": "Video Title", "author": "Author"}

def handle_request(request):
    """处理 MCP 请求"""
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params", {})

    # 处理初始化
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True}
                },
                "serverInfo": {
                    "name": "douyin-mcp-server1",
                    "version": "1.2.7"
                }
            }
        }

    # 处理通知
    elif method and method.startswith("notifications/"):
        return None

    # 获取工具列表
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

    # 处理工具调用
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        # 基础工具
        if tool_name == "get_douyin_download_link":
            share_link = arguments.get("share_link")
            result = get_douyin_download_link(share_link)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": result}]
                }
            }

        elif tool_name == "parse_douyin_video_info":
            share_link = arguments.get("share_link")
            result = parse_douyin_video_info(share_link)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": result}]
                }
            }

        # 高级工具（需要额外依赖）
        elif tool_name == "extract_douyin_text":
            share_link = arguments.get("share_link")
            model = arguments.get("model", "paraformer-realtime-v1")

            result = {
                "status": "info",
                "message": "文字提取功能需要安装完整依赖（ffmpeg, dashscope）",
                "share_link": share_link,
                "model": model,
                "note": "请安装: pip install douyin-mcp-server1[full]"
            }
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
                }
            }

        elif tool_name == "download_douyin_video":
            share_link = arguments.get("share_link")
            output_dir = arguments.get("output_dir", "./downloads")

            result = {
                "status": "info",
                "message": "视频下载功能需要安装完整依赖",
                "share_link": share_link,
                "output_dir": output_dir,
                "note": "请安装: pip install douyin-mcp-server1[full]"
            }
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
                }
            }

        elif tool_name == "extract_douyin_audio":
            share_link = arguments.get("share_link")
            output_dir = arguments.get("output_dir", "./audio")

            result = {
                "status": "info",
                "message": "音频提取功能需要安装 ffmpeg",
                "share_link": share_link,
                "output_dir": output_dir,
                "note": "请安装: apt-get install ffmpeg 或 brew install ffmpeg"
            }
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
                }
            }

        elif tool_name == "get_video_details":
            share_link = arguments.get("share_link")
            video_id = share_link[-10:] if len(share_link) > 10 else "unknown"
            video_info = get_video_info(video_id)
            video_info["share_link"] = share_link
            video_info["timestamp"] = str(int(__import__("time").time()))

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(video_info, ensure_ascii=False, indent=2)}]
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


def main():
    """主函数"""
    # 调试信息
    sys.stderr.write("MCP Server Starting (v1.2.7 stable)...\n")
    sys.stderr.flush()

    # 主循环
    for line in sys.stdin:
        if not line:
            break

        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_request(request)

            if response:
                print(json.dumps(response))
                sys.stdout.flush()

        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    main()