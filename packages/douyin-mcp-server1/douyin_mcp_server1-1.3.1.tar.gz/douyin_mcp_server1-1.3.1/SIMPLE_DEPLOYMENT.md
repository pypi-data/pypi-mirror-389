# 简化部署方案 - 版本 1.3.0

## 核心文件结构

```
douyin_mcp_server1/
├── __init__.py        # 主入口文件（包含所有6个工具）
├── tools.py           # 工具函数（可选）
├── processor.py       # 处理器（可选）
└── server.py          # 完整版服务器（可选）
```

## 部署配置

### 方案1：使用 uvx（推荐）

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["--index-url", "https://pypi.org/simple", "douyin-mcp-server1==1.3.0"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

### 方案2：直接使用源码

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "python3",
      "args": ["/path/to/douyin-mcp-server/douyin_mcp_server1/__init__.py"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

### 方案3：本地 wheel 文件

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["/path/to/douyin_mcp_server1-1.3.0-py3-none-any.whl"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

## 6个工具列表

1. **get_douyin_download_link** - 获取抖音无水印下载链接
2. **parse_douyin_video_info** - 解析抖音视频基本信息
3. **extract_douyin_text** - 语音转文字（需要 DASHSCOPE_API_KEY）
4. **download_douyin_video** - 下载视频到本地
5. **extract_douyin_audio** - 提取音频（需要 ffmpeg）
6. **get_video_details** - 获取视频详细信息

## 验证部署

```bash
# 测试工具数量
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | uvx douyin-mcp-server1==1.3.0

# 应该看到 6 个工具
```

## 依赖说明

### 基础版（2个工具可用）
- 只需基础依赖（mcp, requests）

### 完整版（所有6个工具可用）
```bash
pip install douyin-mcp-server1[full]
```

额外依赖：
- `ffmpeg` - 系统级安装
- `dashscope` - 语音识别
- `ffmpeg-python` - Python 绑定
- `tqdm` - 进度条

## 核心修改

1. **简化入口**：`pyproject.toml` 入口改为 `douyin_mcp_server1:main`
2. **合并逻辑**：所有6个工具都在 `__init__.py` 中定义
3. **无外部依赖**：基础功能只需要 `mcp` 和 `requests`
4. **清晰架构**：单一文件包含所有必要逻辑

## 故障排除

如果 "connection closed" 错误：
1. 使用 `--index-url https://pypi.org/simple` 强制官方源
2. 等待 PyPI 镜像同步
3. 使用本地 wheel 文件
4. 直接运行 Python 脚本

## 根本原因

之前的问题：
- 入口指向复杂的 `mcp_server_simple.py`（14000+行）
- 文件版本混乱
- 依赖 FastMCP 导致额外要求

现在解决：
- 简化为单一入口 `__init__.py`
- 只包含必要功能
- 基础版无额外依赖