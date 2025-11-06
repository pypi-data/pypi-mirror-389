#!/usr/bin/env python3
"""
MCP 服务器主入口 - 使用标准 MCP 库
"""
import asyncio
import json
import sys
from typing import Any, Dict, List

# 导入工具函数
from .tools import get_douyin_download_link, extract_douyin_text, parse_douyin_video_info


class MCPServer:
    """标准的 MCP 服务器实现"""

    def __init__(self):
        self.processor = None
        self.initialized = False

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 MCP 请求"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "initialize":
                # 初始化
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
                            "version": "1.2.0"
                        }
                    }
                }

            elif method == "tools/list":
                # 返回工具列表
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
                        "name": "extract_douyin_text",
                        "description": "从抖音视频提取文本内容",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "share_link": {
                                    "type": "string",
                                    "description": "抖音分享链接"
                                },
                                "model": {
                                    "type": "string",
                                    "description": "语音识别模型（可选）",
                                    "default": "paraformer-v2"
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
                # 调用工具
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                # 获取 API 密钥
                api_key = None
                if "DASHSCOPE_API_KEY" in params.get("_meta", {}):
                    api_key = params["_meta"]["DASHSCOPE_API_KEY"]
                else:
                    import os
                    api_key = os.getenv("DASHSCOPE_API_KEY")

                if not api_key and tool_name == "extract_douyin_text":
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": "未设置 DASHSCOPE_API_KEY"
                        }
                    }

                # 初始化处理器
                if not self.processor:
                    self.processor = DouyinProcessor(api_key or "")

                # 执行相应的工具
                try:
                    if tool_name == "get_douyin_download_link":
                        from .server import get_douyin_download_link
                        result = get_douyin_download_link(arguments["share_link"])
                    elif tool_name == "extract_douyin_text":
                        from .server import extract_douyin_text
                        # 需要异步调用
                        result = await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: asyncio.run(extract_douyin_text(
                                arguments["share_link"],
                                arguments.get("model"),
                                type('Context', (), {
                                    'info': lambda x: None,
                                    'error': lambda x: None,
                                    'report_progress': lambda a, b: None
                                })()
                            ))
                        )
                    elif tool_name == "parse_douyin_video_info":
                        from .server import parse_douyin_video_info
                        result = parse_douyin_video_info(arguments["share_link"])
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"未知工具: {tool_name}"
                            }
                        }

                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": result
                                }
                            ]
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
                    "message": f"内部错误: {str(e)}"
                }
            }


def main():
    """主函数 - 处理 stdio 通信"""
    import asyncio

    async def run_server():
        server = MCPServer()

        try:
            # 读取 stdin 并处理请求
            while True:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )

                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    response = await server.handle_request(request)

                    # 写入响应
                    response_json = json.dumps(response, ensure_ascii=False) + "\n"
                    sys.stdout.write(response_json)
                    sys.stdout.flush()

                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

        except KeyboardInterrupt:
            pass

    # 运行服务器
    asyncio.run(run_server())


if __name__ == "__main__":
    main()