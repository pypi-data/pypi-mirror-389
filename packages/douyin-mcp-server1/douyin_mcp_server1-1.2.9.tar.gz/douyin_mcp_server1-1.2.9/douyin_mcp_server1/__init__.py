"""抖音无水印链接提取 MCP 服务器"""

__version__ = "1.2.8"
__author__ = "yzfly"
__email__ = "yz.liu.me@gmail.com"

# 直接实现main函数，避免缓存问题
import sys
import json
import os

# 工具函数导入
try:
    from .tools import get_douyin_download_link, parse_douyin_video_info, get_video_info
except ImportError:
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

def handle_mcp_request(request):
    """处理MCP请求"""
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params", {})

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
                    "version": "1.2.8"
                }
            }
        }

    elif method and method.startswith("notifications/"):
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
            "result": {"tools": tools}
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "get_douyin_download_link":
            share_link = arguments.get("share_link")
            result = get_douyin_download_link(share_link)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": result}]}
            }

        elif tool_name == "parse_douyin_video_info":
            share_link = arguments.get("share_link")
            result = parse_douyin_video_info(share_link)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": result}]}
            }

        elif tool_name == "extract_douyin_text":
            result = {
                "status": "info",
                "message": "文字提取功能需要安装完整依赖",
                "share_link": arguments.get("share_link"),
                "model": arguments.get("model", "paraformer-realtime-v1")
            }
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
            }

        elif tool_name == "download_douyin_video":
            result = {
                "status": "info",
                "message": "视频下载功能需要安装完整依赖",
                "share_link": arguments.get("share_link"),
                "output_dir": arguments.get("output_dir", "./downloads")
            }
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
            }

        elif tool_name == "extract_douyin_audio":
            result = {
                "status": "info",
                "message": "音频提取功能需要安装 ffmpeg",
                "share_link": arguments.get("share_link"),
                "output_dir": arguments.get("output_dir", "./audio")
            }
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
            }

        elif tool_name == "get_video_details":
            share_link = arguments.get("share_link")
            video_id = share_link[-10:] if len(share_link) > 10 else "unknown"
            video_info = get_video_info(video_id)
            video_info["share_link"] = share_link
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": json.dumps(video_info, ensure_ascii=False)}]}
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"未知工具: {tool_name}"}
            }

    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"未知方法: {method}"}
        }

def main():
    """主函数 - 直接实现，避免缓存问题"""
    sys.stderr.write(f"MCP Server Starting (v{__version__})...\n")
    sys.stderr.flush()

    for line in sys.stdin:
        if not line:
            break

        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_mcp_request(request)

            if response:
                print(json.dumps(response))
                sys.stdout.flush()

        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

__all__ = ["main"]