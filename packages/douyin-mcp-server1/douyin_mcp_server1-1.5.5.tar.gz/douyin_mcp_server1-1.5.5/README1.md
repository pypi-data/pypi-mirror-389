# 抖音无水印视频文本提取 MCP 服务器 1

[![PyPI version](https://badge.fury.io/py/douyin-mcp-server1.svg)](https://badge.fury.io/py/douyin-mcp-server1)
[![Python version](https://img.shields.io/pypi/pyversions/douyin-mcp-server1.svg)](https://pypi.org/project/douyin-mcp-server1/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

一个基于 Model Context Protocol (MCP) 的服务器，可以从抖音分享链接下载无水印视频，智能提取音频并转换为文本。

## 🎯 版本 1.2.0 更新内容

### ✨ 新增功能
- **智能音频压缩** - 自动将音频压缩到 50MB 以内，最大化保留音质
- **并发安全** - 支持多进程并发调用，每个实例使用独立临时目录
- **错误恢复** - 完善的异常处理机制，确保资源正确清理
- **精确时长检测** - 自动检测音频时长，精确计算压缩参数

### 🔧 优化改进
- 修复了 "Multimodal file size is too large" 错误
- 改进 API 调用方式，使用本地文件上传
- 四级压缩策略，智能选择最佳音质
- 线程安全的文件管理系统

## 🚀 快速开始

### 使用 uvx 安装（推荐）

```bash
# 安装最新版本
uvx install douyin-mcp-server1

# 或者指定版本
uvx install douyin-mcp-server1==1.2.0
```

### 手动安装

```bash
pip install douyin-mcp-server1
```

### 配置环境变量

在 Claude Desktop、Cherry Studio 等支持 MCP Server 的应用配置文件中添加：

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["douyin-mcp-server1"],
      "env": {
        "DASHSCOPE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## 📋 功能特性

- 🎵 **无水印视频获取** - 从抖音分享链接获取高质量无水印视频
- 🎧 **智能音频提取** - 自动从视频中提取音频内容
- 🔥 **智能压缩** - 自动压缩音频到 50MB 以内，满足 API 限制
- 📝 **AI 文本识别** - 使用阿里云百炼 API 提取文本内容
- 🧹 **自动清理** - 智能清理处理过程中的临时文件
- 🔄 **并发安全** - 支持多进程并发，文件隔离
- ⚡ **错误恢复** - 完善的异常处理和资源清理

## 🛠️ 使用方法

### 1. 获取无水印下载链接

```python
from douyin_mcp_server1 import get_douyin_download_link

# 从分享链接获取下载地址
result = get_douyin_download_link("https://v.douyin.com/xxxxxxxx/")
```

### 2. 提取视频文本内容

```python
from douyin_mcp_server1 import extract_douyin_text

# 需要设置环境变量 DASHSCOPE_API_KEY
text = extract_douyin_text("https://v.douyin.com/xxxxxxxx/")
print(text)
```

### 3. 解析视频信息

```python
from douyin_mcp_server1 import parse_douyin_video_info

# 获取视频基本信息
info = parse_douyin_video_info("https://v.douyin.com/xxxxxxxx/")
```

## ⚙️ 依赖要求

- Python >= 3.10
- ffmpeg（系统级依赖）

### 安装 ffmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
下载并安装 [ffmpeg](https://ffmpeg.org/download.html)

## 📖 API 密钥配置

前往 [阿里云百炼](https://help.aliyun.com/zh/model-studio/get-api-key?) 获取 API 密钥：

```bash
export DASHSCOPE_API_KEY="your_api_key_here"
```

## 🔍 技术细节

### 音频压缩策略

系统采用四级压缩策略，确保在 50MB 限制内保留最佳音质：

1. **第一级** - 保持 44.1kHz 立体声，适当降低比特率
2. **第二级** - 降低到 22.05kHz 立体声
3. **第三级** - 16kHz 单声道
4. **第四级** - 16kHz 单声道 32kbps（极限模式）

### 并发安全机制

- 每个处理器实例使用独立的临时目录
- 目录命名包含进程 ID 和 UUID
- 线程安全的文件管理系统
- 自动清理，不影响其他进程

## 📄 许可证

本项目基于 Apache 2.0 协议发布。详见 [LICENSE](LICENSE) 文件。

## ⚠️ 免责声明

1. 本项目仅供学习和研究使用
2. 使用本项目需遵守相关法律法规
3. 作者不对使用本项目产生的任何后果负责
4. 请尊重内容版权，合理使用

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

如有问题，请通过 GitHub Issues 反馈。