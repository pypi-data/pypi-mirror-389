#!/usr/bin/env python3
"""
最小化 MCP 服务器 - 用于调试部署问题
"""
import sys
import json
import os

def main():
    """主函数"""
    # 设置环境变量
    if not os.environ.get('DASHSCOPE_API_KEY'):
        os.environ['DASHSCOPE_API_KEY'] = 'test_key'

    # 写入调试信息
    sys.stderr.write(f"DEBUG: Server starting with Python {sys.version}\n")
    sys.stderr.write(f"DEBUG: Args: {sys.argv}\n")
    sys.stderr.write(f"DEBUG: CWD: {os.getcwd()}\n")
    sys.stderr.flush()

    # 主循环
    try:
        for line in sys.stdin:
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                method = request.get("method")
                request_id = request.get("id")

                if method == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {"listChanged": True}
                            },
                            "serverInfo": {
                                "name": "douyin-mcp-server1",
                                "version": "1.2.4"
                            }
                        }
                    }
                    print(json.dumps(response))
                    sys.stdout.flush()

                elif method == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "tools": [
                                {
                                    "name": "test_tool",
                                    "description": "A test tool",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {},
                                        "required": []
                                    }
                                }
                            ]
                        }
                    }
                    print(json.dumps(response))
                    sys.stdout.flush()

                elif method == "tools/call":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Test response"
                                }
                            ]
                        }
                    }
                    print(json.dumps(response))
                    sys.stdout.flush()

            except json.JSONDecodeError:
                sys.stderr.write(f"DEBUG: JSON decode error for: {line}\n")
                sys.stderr.flush()
            except Exception as e:
                sys.stderr.write(f"DEBUG: Error processing request: {e}\n")
                sys.stderr.flush()

    except KeyboardInterrupt:
        sys.stderr.write("DEBUG: Server shutting down\n")
        sys.stderr.flush()

if __name__ == "__main__":
    main()