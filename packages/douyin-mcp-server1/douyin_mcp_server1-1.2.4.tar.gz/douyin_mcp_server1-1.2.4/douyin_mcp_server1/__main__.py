#!/usr/bin/env python3
"""
MCP 服务器主入口点
"""

def main():
    """启动MCP服务器"""
    from .mcp_server_simple import main as mcp_main
    mcp_main()

if __name__ == "__main__":
    main()