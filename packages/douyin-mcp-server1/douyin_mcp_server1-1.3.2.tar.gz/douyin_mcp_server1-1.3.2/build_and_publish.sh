#!/bin/bash
# 构建和发布 douyin-mcp-server1

set -e  # 遇到错误立即退出

echo "=========================================="
echo "抖音 MCP 服务器 - 构建和发布脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."

    # 检查 uv
    if ! command -v uv &> /dev/null; then
        print_error "uv 未安装，请先安装 uv: pip install uv"
        exit 1
    fi

    # 检查 twine
    if ! python -m pip show twine &> /dev/null; then
        print_info "安装 twine..."
        python -m pip install twine
    fi
}

# 清理旧文件
clean() {
    print_info "清理旧的构建文件..."
    rm -rf dist/ build/ *.egg-info/
}

# 构建包
build() {
    print_info "构建包..."

    # 使用 uv 构建
    if command -v uv &> /dev/null && uv --version | grep -q "0.4"; then
        print_info "使用 uv 构建..."
        uv build
    else
        # 回退到 pip
        print_info "使用 pip 构建..."
        python -m pip install --upgrade build
        python -m build
    fi
}

# 检查包
check() {
    print_info "检查包..."
    python -m twine check dist/*
}

# 上传到测试 PyPI
upload_test() {
    read -p "是否上传到测试 PyPI？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "上传到测试 PyPI..."
        python -m twine upload --repository testpypi dist/*
        print_warning "测试安装命令:"
        print_warning "pip install -i https://test.pypi.org/simple/ douyin-mcp-server1"
    fi
}

# 上传到正式 PyPI
upload() {
    read -p $'\033[1;33m⚠️  确认上传到正式 PyPI？(y/N): \033[0m' -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "上传到 PyPI..."
        python -m twine upload dist/*
        print_info "✅ 发布成功！"
        echo
        print_info "安装命令:"
        print_info "  pip install douyin-mcp-server1"
        print_info ""
        print_info "uvx 命令:"
        print_info "  uvx install douyin-mcp-server1"
    else
        print_warning "发布已取消"
        exit 0
    fi
}

# 测试 uvx
test_uvx() {
    print_info "测试 uvx 安装..."

    # 创建临时测试目录
    TEMP_DIR=$(mktemp -d)
    cd $TEMP_DIR

    # 测试 uvx 安装
    if uvx --help &> /dev/null; then
        print_info "uvx 可用，测试安装..."
        uvx --verbose douyin-mcp-server1 --help || true
        print_info "✅ uvx 测试完成"
    else
        print_warning "uvx 不可用，跳过测试"
    fi

    # 清理
    cd -
    rm -rf $TEMP_DIR
}

# 主流程
main() {
    print_info "开始构建和发布 douyin-mcp-server1..."

    # 检查是否在项目根目录
    if [ ! -f "pyproject.toml" ]; then
        print_error "请在项目根目录运行此脚本"
        exit 1
    fi

    # 显示当前版本
    VERSION=$(python -c "import toml; c=toml.load('pyproject.toml'); print(c['project']['version'])")
    print_info "当前版本: $VERSION"

    # 确认继续
    read -p "确认继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "操作已取消"
        exit 0
    fi

    # 执行步骤
    check_dependencies
    clean
    build
    check

    # 上传
    upload_test
    upload

    # 可选测试
    read -p $'\n是否测试 uvx 安装？(y/N): ' -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_uvx
    fi

    print_info "🎉 完成！"
}

# 错误处理
trap 'print_error "脚本执行失败！"; exit 1' ERR

# 运行主函数
main "$@"