"""抖音无水印链接提取 MCP 服务器"""

__version__ = "1.4.2"
__author__ = "yzfly"
__email__ = "yz.liu.me@gmail.com"

# 使用FastMCP版本，完全按照原版结构
from .server_fastmcp import main

__all__ = ["main"]