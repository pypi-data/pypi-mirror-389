#!/usr/bin/env python3
"""
简化的 MCP 服务器实现
"""
import json
import sys
import os
import traceback
from pathlib import Path

# 导入工具函数
try:
    from douyin_mcp_server1.tools import get_douyin_download_link, extract_douyin_text, parse_douyin_video_info
except ImportError:
    # 开发环境导入
    sys.path.insert(0, str(Path(__file__).parent))
    from douyin_mcp_server1.tools import get_douyin_download_link, extract_douyin_text, parse_douyin_video_info


def log_error(message):
    """记录错误到 stderr"""
    print(f"ERROR: {message}", file=sys.stderr)


def handle_request(request):
    """处理 MCP 请求"""
    try:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        # 处理初始化
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "douyin-mcp-server1",
                        "version": "1.2.1"
                    }
                }
            }

        # 处理工具列表
        elif method == "tools/list":
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
                        }
                    ]
                }
            }

        # 处理工具调用
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            try:
                if tool_name == "get_douyin_download_link":
                    result = get_douyin_download_link(arguments["share_link"])
                elif tool_name == "parse_douyin_video_info":
                    result = parse_douyin_video_info(arguments["share_link"])
                elif tool_name == "extract_douyin_text":
                    # 检查 API 密钥
                    if not os.getenv("DASHSCOPE_API_KEY"):
                        raise ValueError("未设置 DASHSCOPE_API_KEY")

                    # 同步调用异步函数（需要简化）
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    # 创建一个简单的上下文对象
                    class SimpleContext:
                        def info(self, msg): pass
                        def error(self, msg): pass
                        def report_progress(self, a, b): pass

                    result = loop.run_until_complete(
                        extract_douyin_text(
                            arguments["share_link"],
                            arguments.get("model"),
                            SimpleContext()
                        )
                    )
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

        # 其他方法
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
        log_error(f"处理请求失败: {str(e)}\n{traceback.format_exc()}")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": "内部服务器错误"
            }
        }


def main():
    """主函数"""
    try:
        # 调试信息
        log_error("MCP 服务器启动中...")

        # 主循环
        while True:
            try:
                # 读取一行输入
                line = sys.stdin.readline()

                if not line:
                    # EOF，正常退出
                    break

                line = line.strip()
                if not line:
                    continue

                # 解析 JSON
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    log_error(f"JSON 解析错误: {e}")
                    continue

                # 处理请求
                response = handle_request(request)

                # 输出响应
                response_line = json.dumps(response, ensure_ascii=False) + "\n"
                sys.stdout.write(response_line)
                sys.stdout.flush()

            except KeyboardInterrupt:
                break
            except Exception as e:
                log_error(f"处理循环错误: {e}")
                continue

    except Exception as e:
        log_error(f"服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()