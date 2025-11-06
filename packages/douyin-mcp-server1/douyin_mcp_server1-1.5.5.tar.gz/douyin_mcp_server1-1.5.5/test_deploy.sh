#!/bin/bash
# 测试部署配置

echo "测试官方源..."
uvx --index-url https://pypi.org/simple --no-cache douyin-mcp-server1==1.4.6 --help 2>&1 | head -10

echo -e "\n\n测试多源配置..."
uvx --index-strategy unsafe-best-match --index-url https://pypi.org/simple --extra-index-url https://mirrors.aliyun.com/pypi/simple/ douyin-mcp-server1==1.4.6 --help 2>&1 | head -10