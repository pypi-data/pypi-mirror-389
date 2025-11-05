"""抖音无水印链接提取 MCP 服务器"""

__version__ = "1.4.4"
__author__ = "yzfly"
__email__ = "yz.liu.me@gmail.com"

# 使用最终版本，不依赖FastMCP
from .server_final import main

__all__ = ["main"]