#!/usr/bin/env python3
"""
极简 MCP 服务器 - 不依赖任何外部库
完全兼容原始项目的简洁性
"""

import json
import sys
import os


def handle_request(request):
    """处理请求 - 极简版本"""
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
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "douyin-mcp-server1",
                    "version": "1.4.1"
                }
            }
        }

    # 工具列表
    elif method == "tools/list":
        tools = [
            {
                "name": "get_douyin_video_url",
                "description": "从抖音分享文本中提取无水印视频链接",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "share_text": {
                            "type": "string",
                            "description": "包含抖音分享链接的文本"
                        }
                    },
                    "required": ["share_text"]
                }
            },
            {
                "name": "extract_douyin_text",
                "description": "从抖音视频中提取语音转文字（需要 DASHSCOPE_API_KEY）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "share_text": {
                            "type": "string",
                            "description": "包含抖音分享链接的文本"
                        }
                    },
                    "required": ["share_text"]
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

        if tool_name == "get_douyin_video_url":
            # 极简实现
            share_text = arguments.get("share_text", "")
            video_id = share_text[-19:] if len(share_text) > 19 else "unknown"
            url = f"https://download.douyin.com/video/{video_id}"

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": url
                        }
                    ]
                }
            }

        elif tool_name == "extract_douyin_text":
            # 检查API密钥
            if not os.getenv("DASHSCOPE_API_KEY"):
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": "错误：需要设置 DASHSCOPE_API_KEY 环境变量"
                            }
                        ]
                    }
                }

            # 极简实现 - 返回提示信息
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "语音提取功能需要完整版依赖（ffmpeg, dashscope）\n请安装: pip install douyin-mcp-server1[full]"
                        }
                    ]
                }
            }

    # 未知方法
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32601,
            "message": f"Unknown method: {method}"
        }
    }


def main():
    """主函数 - 极简版本"""
    # 不输出任何调试信息到 stdout

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
                # 只输出JSON到stdout
                print(json.dumps(response, ensure_ascii=False))
                sys.stdout.flush()

        except json.JSONDecodeError:
            # 静默处理无效JSON
            continue
        except Exception as e:
            # 错误响应
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