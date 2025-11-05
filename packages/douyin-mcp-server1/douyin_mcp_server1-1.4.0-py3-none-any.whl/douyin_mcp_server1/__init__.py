"""抖音无水印链接提取 MCP 服务器 - 增强版本"""

__version__ = "1.4.0"
__author__ = "yzfly"
__email__ = "yz.liu.me@gmail.com"

# 使用 FastMCP 方式
from .server import main

__all__ = ["main"]