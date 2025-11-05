"""抖音无水印链接提取 MCP 服务器 - 极简版本"""

__version__ = "1.4.1"
__author__ = "yzfly"
__email__ = "yz.liu.me@gmail.com"

# 使用极简版本，不依赖任何外部库
from .minimal_server import main

__all__ = ["main"]