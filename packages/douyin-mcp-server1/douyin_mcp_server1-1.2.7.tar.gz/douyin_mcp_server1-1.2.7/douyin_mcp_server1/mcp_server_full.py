#!/usr/bin/env python3
"""
完整的 MCP 服务器实现
包含所有工具功能
"""
import sys
import json
import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# 导入工具函数
from .processor import DouyinProcessor
from .tools import get_video_info


class FullMCPServer:
    """完整的MCP服务器"""

    def __init__(self):
        self.server = Server("douyin-mcp-server1", version="1.2.6")
        self.processor = None

        # 注册工具
        self.register_tools()

    def register_tools(self):
        """注册所有工具"""

        # 工具1: 获取抖音下载链接
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="get_douyin_download_link",
                    description="获取抖音视频的无水印下载链接",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "share_link": {
                                "type": "string",
                                "description": "抖音分享链接"
                            }
                        },
                        "required": ["share_link"]
                    }
                ),
                Tool(
                    name="parse_douyin_video_info",
                    description="解析抖音视频基本信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "share_link": {
                                "type": "string",
                                "description": "抖音分享链接"
                            }
                        },
                        "required": ["share_link"]
                    }
                ),
                Tool(
                    name="extract_douyin_text",
                    description="从抖音视频中提取语音转文字",
                    inputSchema={
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
                ),
                Tool(
                    name="download_douyin_video",
                    description="下载抖音视频到本地",
                    inputSchema={
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
                ),
                Tool(
                    name="extract_douyin_audio",
                    description="从抖音视频中提取音频",
                    inputSchema={
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
                ),
                Tool(
                    name="get_video_details",
                    description="获取抖音视频详细信息（包括作者、文案等）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "share_link": {
                                "type": "string",
                                "description": "抖音分享链接"
                            }
                        },
                        "required": ["share_link"]
                    }
                )
            ]

        # 处理工具调用
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> list[TextContent]:
            try:
                # 初始化处理器
                if not self.processor:
                    self.processor = DouyinProcessor()

                if name == "get_douyin_download_link":
                    share_link = arguments.get("share_link")
                    from .tools import get_douyin_download_link
                    result = get_douyin_download_link(share_link)
                    return [TextContent(type="text", text=result)]

                elif name == "parse_douyin_video_info":
                    share_link = arguments.get("share_link")
                    from .tools import parse_douyin_video_info
                    result = parse_douyin_video_info(share_link)
                    return [TextContent(type="text", text=result)]

                elif name == "extract_douyin_text":
                    share_link = arguments.get("share_link")
                    model = arguments.get("model", "paraformer-realtime-v1")

                    # 使用 processor 提取文字
                    if not self.processor:
                        self.processor = DouyinProcessor()

                    result = await self.processor.extract_text_from_video(share_link, model=model)
                    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

                elif name == "download_douyin_video":
                    share_link = arguments.get("share_link")
                    output_dir = arguments.get("output_dir", "./downloads")

                    # 获取视频信息并下载
                    video_id = self._extract_video_id(share_link)
                    video_info = get_video_info(video_id)

                    if self.processor:
                        download_path = await self.processor.download_video(video_info, ctx=None)
                        return [TextContent(type="text", text=f"视频已下载到: {download_path}")]
                    else:
                        return [TextContent(type="text", text="下载功能暂不可用")]

                elif name == "extract_douyin_audio":
                    share_link = arguments.get("share_link")
                    output_dir = arguments.get("output_dir", "./audio")

                    # 实现音频提取
                    video_id = self._extract_video_id(share_link)
                    video_info = get_video_info(video_id)

                    if self.processor:
                        audio_path = await self.processor.extract_audio_only(video_info)
                        return [TextContent(type="text", text=f"音频已提取到: {audio_path}")]
                    else:
                        return [TextContent(type="text", text="音频提取功能暂不可用")]

                elif name == "get_video_details":
                    share_link = arguments.get("share_link")

                    # 获取详细信息
                    video_id = self._extract_video_id(share_link)
                    video_info = get_video_info(video_id)

                    # 尝试获取更详细的信息
                    try:
                        import requests
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        response = requests.get(share_link, headers=headers, timeout=10)
                        # 这里可以解析更多详细信息
                    except:
                        pass

                    return [TextContent(type="text", text=json.dumps(video_info, ensure_ascii=False, indent=2))]

                else:
                    return [TextContent(type="text", text=f"未知工具: {name}")]

            except Exception as e:
                return [TextContent(type="text", text=f"错误: {str(e)}")]

    def _extract_video_id(self, share_link: str) -> str:
        """从分享链接中提取视频ID"""
        # 简单的ID提取逻辑
        if "/video/" in share_link:
            return share_link.split("/video/")[1].split("?")[0]
        return share_link


async def main():
    """主函数"""
    import sys

    # 创建服务器实例
    mcp_server = FullMCPServer()

    # 使用stdio传输
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        session = ClientSession(read_stream, write_stream)
        await session.initialize()

        # 运行服务器
        await mcp_server.server.run(
            session,
            NotificationOptions(),
        )


def main_sync():
    """同步入口点"""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()