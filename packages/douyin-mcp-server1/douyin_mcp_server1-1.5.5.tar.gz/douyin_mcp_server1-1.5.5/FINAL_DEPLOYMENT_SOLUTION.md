# 最终部署解决方案

## 问题总结

经过深入分析，发现了以下问题：

1. **工具数量问题**：只显示2个工具而不是6个
   - 原因：pyproject.toml 入口点指向的 `mcp_server_simple.py` 只包含2个工具
   - 已解决：更新 `mcp_server_simple.py` 包含所有6个工具

2. **MCP接口参数问题**：
   - extract_douyin_text 等高级工具的参数正确解析
   - 已解决：所有工具都有完整的 inputSchema 定义

## 立即可用的解决方案

### 方案1：使用最新版本 1.2.9（推荐）

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["--index-url", "https://pypi.org/simple", "douyin-mcp-server1==1.2.9"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

### 方案2：使用本地wheel文件

如果 PyPI 镜像问题，可以使用本地文件：

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["/app/test/douyin-mcp-server/dist/douyin_mcp_server1-1.2.9-py3-none-any.whl"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

### 方案3：直接使用源码

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "python3",
      "args": ["/app/test/douyin-mcp-server/douyin_mcp_server1/mcp_server_simple.py"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

## 6个工具列表

版本 1.2.9 包含以下6个工具：

1. **get_douyin_download_link** - 获取抖音无水印下载链接
2. **parse_douyin_video_info** - 解析抖音视频基本信息
3. **extract_douyin_text** - 从抖音视频中提取语音转文字（需要完整依赖）
4. **download_douyin_video** - 下载抖音视频到本地（需要完整依赖）
5. **extract_douyin_audio** - 从抖音视频中提取音频（需要 ffmpeg）
6. **get_video_details** - 获取抖音视频详细信息

## 完整功能依赖

要使用所有功能，需要安装：

```bash
# 基础依赖（2个工具可用）
pip install douyin-mcp-server1==1.2.9

# 完整功能依赖（所有6个工具可用）
pip install douyin-mcp-server1[full]
```

或单独安装：
- `ffmpeg` - 用于视频/音频处理（系统级）
- `dashscope` - 用于语音转文字
- `ffmpeg-python` - Python ffmpeg 绑定
- `tqdm` - 进度条

## 验证部署

部署后可以通过以下命令验证工具数量：

```bash
# 应该返回6个工具
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | uvx douyin-mcp-server1==1.2.9
```

## MCP接口参数说明

所有工具都支持标准 MCP JSON-RPC 接口：

### 输入格式
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "工具名称",
    "arguments": {
      "share_link": "抖音分享链接",
      "其他参数": "值"
    }
  }
}
```

### 输出格式
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "JSON格式的结果"
      }
    ]
  }
}
```

## 虚拟环境说明

**MCP 服务器本身不创建虚拟环境**，但部署方式会影响：

1. **uvx 部署**：自动创建临时虚拟环境
2. **pip 部署**：使用当前环境的虚拟环境（如果有）
3. **直接运行**：使用当前 Python 环境

推荐使用 uvx，因为它：
- 自动管理依赖
- 隔离环境避免冲突
- 支持版本控制

## 故障排除

如果仍然只有2个工具：
1. 清理 uvx 缓存：`rm -rf ~/.local/share/uv/tools/douyin*`
2. 确保使用版本 1.2.9 或更高
3. 使用 `--index-url https://pypi.org/simple` 强制使用官方源

如果 extract_douyin_text 报错：
1. 确认 `DASHSCOPE_API_KEY` 在 `env` 中设置
2. 安装完整依赖：`pip install douyin-mcp-server1[full]`
3. 安装系统级 ffmpeg

## 成功标志

成功的部署应该：
- ✅ 显示6个工具
- ✅ extract_douyin_text 正确接收 share_link 参数
- ✅ 高级工具提示需要安装依赖（而不是报错）
- ✅ 基础工具（1-2）正常工作
- ✅ 初始化响应版本号 1.2.9

## 核心功能实现

extract_douyin_text 的完整工作流程：
1. 接收抖音分享链接参数
2. 提取无水印视频链接
3. 下载视频到临时目录
4. 使用 ffmpeg 提取音频
5. 压缩音频到50MB内
6. 调用 dashscope API 进行语音识别
7. 清理所有临时文件
8. 返回识别的文字结果