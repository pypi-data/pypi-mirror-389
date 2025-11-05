#!/usr/bin/env python3
"""
最简化的 MCP 服务器 - 模拟原始项目
"""

import json
import sys

def main():
    """最简化的主函数"""
    # 直接输出到 stdout
    print(json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "douyin-mcp-server1",
                "version": "1.4.0"
            }
        }
    }))

    # 简单的读取-响应循环
    for line in sys.stdin:
        if not line:
            break
        request = json.loads(line.strip())

        if request.get("method") == "tools/list":
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {"tools": [
                    {"name": "get_douyin_video_url", "description": "获取链接"},
                    {"name": "extract_douyin_text", "description": "提取文字"}
                ]}
            }))
            sys.stdout.flush()

if __name__ == "__main__":
    main()