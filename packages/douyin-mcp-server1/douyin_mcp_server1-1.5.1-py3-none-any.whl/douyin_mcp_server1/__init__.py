"""抖音无水印链接提取 MCP 服务器"""

__version__ = "1.5.1"
__author__ = "yzfly"
__email__ = "yz.liu.me@gmail.com"

# 使用 FastMCP 版本，完全按照原版
from .server_fastmcp_real import main

__all__ = ["main"]