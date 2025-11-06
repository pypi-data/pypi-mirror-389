#!/bin/bash
# 快速发布脚本 - 请在安全环境中使用

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "抖音 MCP 服务器 - 快速发布"
echo "=========================================="

# 检查目录
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}错误: 请在项目根目录运行${NC}"
    exit 1
fi

# 使用环境变量中的 token
if [ -z "$TWINE_PASSWORD" ]; then
    echo -e "${YELLOW}请设置 TWINE_PASSWORD 环境变量${NC}"
    echo "export TWINE_PASSWORD=\"your-pypi-token\""
    echo "export TWINE_USERNAME=\"__token__\""
    exit 1
fi

# 显示当前配置
echo -e "${GREEN}当前配置:${NC}"
echo "包名: douyin-mcp-server1"
python -c "import toml; c=toml.load('pyproject.toml'); print(f'版本: {c[\"project\"][\"version\"]}')"

# 清理
echo -e "\n${GREEN}清理旧文件...${NC}"
rm -rf dist/ build/ *.egg-info/

# 安装工具
echo -e "\n${GREEN}安装构建工具...${NC}"
python -m pip install --upgrade build twine

# 构建
echo -e "\n${GREEN}构建包...${NC}"
python -m build

# 检查
echo -e "\n${GREEN}检查包...${NC}"
python -m twine check dist/*

# 发布
echo -e "\n${GREEN}发布到 PyPI...${NC}"
python -m twine upload dist/*

echo -e "\n${GREEN}🎉 发布成功！${NC}"
echo ""
echo "安装命令:"
echo "  pip install douyin-mcp-server1"
echo "  uvx install douyin-mcp-server1"