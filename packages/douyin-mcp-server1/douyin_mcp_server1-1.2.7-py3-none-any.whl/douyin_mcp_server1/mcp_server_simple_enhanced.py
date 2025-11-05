#!/usr/bin/env python3
"""
增强版简化 MCP 服务器 - 包含所有6个工具
不依赖外部框架，直接处理 JSON-RPC
"""
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

# 工具函数导入
try:
    from .tools import (
        get_douyin_download_link,
        parse_douyin_video_info,
        get_video_info
    )
    from .processor import DouyinProcessor
except ImportError:
    # 如果导入失败，提供测试实现
    def get_douyin_download_link(share_link: str) -> str:
        return json.dumps({
            "status": "success",
            "download_url": "https://example.com/video.mp4",
            "message": "获取下载链接成功（测试模式）"
        }, ensure_ascii=False)

    def parse_douyin_video_info(share_link: str) -> str:
        return json.dumps({
            "status": "success",
            "video_info": {
                "title": "测试视频",
                "author": "测试用户",
                "duration": "30s"
            },
            "message": "解析视频信息成功（测试模式）"
        }, ensure_ascii=False)

    def get_video_info(video_id: str) -> Dict[str, Any]:
        return {
            "video_id": video_id,
            "title": "测试视频",
            "author": "测试用户"
        }


class SimpleMCPServer:
    """简化的 MCP 服务器实现"""

    def __init__(self):
        self.processor = None

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理JSON-RPC请求"""
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})

        try:
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

            # 通知不需要响应
            elif method and method.startswith("notifications/"):
                # 不返回任何响应
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
                        "description": "获取抖音视频详细信息（包括作者、文案等）",
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

            # 调用工具
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                return self._handle_tool_call(tool_name, arguments, request_id)

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

    def _handle_tool_call(self, tool_name: str, arguments: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """处理工具调用"""
        try:
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

            elif tool_name == "extract_douyin_text":
                share_link = arguments.get("share_link")
                model = arguments.get("model", "paraformer-realtime-v1")

                # 异步调用文字提取（简化版）
                try:
                    # 初始化处理器
                    if not self.processor:
                        self.processor = DouyinProcessor()

                    # 提取文字
                    result = self.processor.extract_text_from_video_sync(share_link, model)
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
                        }
                    }
                except Exception as e:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [{"type": "text", "text": f"文字提取失败: {str(e)}"}]
                        }
                    }

            elif tool_name == "download_douyin_video":
                share_link = arguments.get("share_link")
                output_dir = arguments.get("output_dir", "./downloads")

                # 提取视频ID
                video_id = self._extract_video_id(share_link)
                video_info = get_video_info(video_id)

                # 尝试下载
                try:
                    if self.processor:
                        # 使用异步方法（但这里简化为同步）
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        download_path = loop.run_until_complete(
                            self.processor.download_video(video_info, ctx=None)
                        )
                        loop.close()

                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"视频已下载到: {download_path}"}]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": "下载功能需要安装完整依赖"}]
                            }
                        }
                except Exception as e:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [{"type": "text", "text": f"下载失败: {str(e)}"}]
                        }
                    }

            elif tool_name == "extract_douyin_audio":
                share_link = arguments.get("share_link")
                output_dir = arguments.get("output_dir", "./audio")

                # 提取音频
                video_id = self._extract_video_id(share_link)
                video_info = get_video_info(video_id)

                try:
                    if self.processor:
                        audio_path = self.processor.extract_audio_only_sync(video_info)
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"音频已提取到: {audio_path}"}]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": "音频提取功能需要安装完整依赖"}]
                            }
                        }
                except Exception as e:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [{"type": "text", "text": f"音频提取失败: {str(e)}"}]
                        }
                    }

            elif tool_name == "get_video_details":
                share_link = arguments.get("share_link")

                # 获取详细信息
                video_id = self._extract_video_id(share_link)
                video_info = get_video_info(video_id)

                # 添加更多详细信息
                video_info.update({
                    "extracted_at": str(Path.cwd()),
                    "share_link": share_link
                })

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

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"工具调用错误: {str(e)}"
                }
            }

    def _extract_video_id(self, share_link: str) -> str:
        """从分享链接中提取视频ID"""
        if "/video/" in share_link:
            return share_link.split("/video/")[1].split("?")[0]
        elif share_link.strip().isdigit():
            return share_link.strip()
        return share_link


def main():
    """主函数 - 启动MCP服务器"""
    # 写入调试信息到stderr
    sys.stderr.write("MCP Server Starting...\n")
    sys.stderr.flush()

    # 创建服务器实例
    server = SimpleMCPServer()

    # 主循环，读取stdin并处理
    try:
        for line in sys.stdin:
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                response = server.handle_request(request)

                # 如果有响应，写入stdout
                if response:
                    print(json.dumps(response))
                    sys.stdout.flush()

            except json.JSONDecodeError:
                # 忽略无法解析的行
                continue
            except Exception as e:
                # 发送错误响应
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

    except KeyboardInterrupt:
        sys.stderr.write("MCP Server Shutting Down...\n")
        sys.stderr.flush()


if __name__ == "__main__":
    main()