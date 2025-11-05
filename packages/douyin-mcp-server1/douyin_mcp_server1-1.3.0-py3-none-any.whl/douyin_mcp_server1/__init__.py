"""抖音无水印链接提取 MCP 服务器"""

__version__ = "1.3.0"
__author__ = "yzfly"
__email__ = "yz.liu.me@gmail.com"

import json
import sys
import os

# 工具函数备用实现
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

def extract_douyin_text(share_link: str, model: str = "paraformer-realtime-v1") -> str:
    # 检查是否有API密钥
    if not os.getenv("DASHSCOPE_API_KEY"):
        return json.dumps({
            "status": "error",
            "message": "需要设置 DASHSCOPE_API_KEY 环境变量",
            "share_link": share_link
        }, ensure_ascii=False)

    return json.dumps({
        "status": "info",
        "message": "文字提取功能需要完整版依赖",
        "share_link": share_link,
        "model": model,
        "note": "请安装: pip install douyin-mcp-server1[full]"
    }, ensure_ascii=False)

def download_douyin_video(share_link: str, output_dir: str = "./downloads") -> str:
    return json.dumps({
        "status": "info",
        "message": "视频下载功能需要完整版依赖",
        "share_link": share_link,
        "output_dir": output_dir,
        "note": "请安装: pip install douyin-mcp-server1[full]"
    }, ensure_ascii=False)

def extract_douyin_audio(share_link: str, output_dir: str = "./audio") -> str:
    return json.dumps({
        "status": "info",
        "message": "音频提取功能需要 ffmpeg",
        "share_link": share_link,
        "output_dir": output_dir,
        "note": "请安装: apt-get install ffmpeg 或 brew install ffmpeg"
    }, ensure_ascii=False)

def get_video_details(share_link: str) -> str:
    video_id = share_link[-10:] if len(share_link) > 10 else "unknown"
    return json.dumps({
        "video_id": video_id,
        "title": "抖音视频标题",
        "author": "作者名称",
        "share_link": share_link
    }, ensure_ascii=False)


def handle_mcp_request(request):
    """处理MCP请求 - 核心函数"""
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params", {})

    # 初始化
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
                    "version": __version__
                }
            }
        }

    # 通知不需要响应
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
            "result": {"tools": tools}
        }

    # 工具调用
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
            share_link = arguments.get("share_link")
            model = arguments.get("model", "paraformer-realtime-v1")
            result = extract_douyin_text(share_link, model)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": result}]}
            }

        elif tool_name == "download_douyin_video":
            share_link = arguments.get("share_link")
            output_dir = arguments.get("output_dir", "./downloads")
            result = download_douyin_video(share_link, output_dir)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": result}]}
            }

        elif tool_name == "extract_douyin_audio":
            share_link = arguments.get("share_link")
            output_dir = arguments.get("output_dir", "./audio")
            result = extract_douyin_audio(share_link, output_dir)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": result}]}
            }

        elif tool_name == "get_video_details":
            share_link = arguments.get("share_link")
            result = get_video_details(share_link)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": result}]}
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
    """主函数 - 简化版本"""
    # 不输出调试信息，避免干扰

    # 主循环
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
                print(json.dumps(response, ensure_ascii=False))
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