# 最终部署解决方案

## 问题总结

经过深入分析，发现了以下问题：

1. **工具数量问题**：只显示2个工具而不是6个
   - 原因：之前部署使用的是简化版本 `mcp_server_simple.py`
   - 已解决：版本 1.2.8 包含所有6个工具

2. **环境变量传递问题**：
   - 错误：`DASHSCOPE_API_KEY` 作为命令行参数传递
   - 正确：必须在 `env` 字段中传递

## 立即可用的解决方案

### 方案1：使用最新版本 1.2.8（推荐）

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["--default-index", "https://pypi.org/simple", "douyin-mcp-server1==1.2.8"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

### 方案2：使用本地wheel文件（如果PyPI镜像问题）

1. 下载wheel文件：
```bash
wget https://files.pythonhosted.org/packages/py3/d/douyin_mcp_server1/douyin_mcp_server1-1.2.8-py3-none-any.whl
```

2. 配置：
```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["/完整路径/douyin_mcp_server1-1.2.8-py3-none-any.whl"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

### 方案3：直接使用源码（如果uvx有问题）

1. 克隆代码：
```bash
git clone https://github.com/yzfly/douyin-mcp-server.git
cd douyin-mcp-server
```

2. 配置：
```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "python3",
      "args": ["/path/to/douyin-mcp-server/douyin_mcp_server1/__init__.py"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥",
        "PYTHONPATH": "/path/to/douyin-mcp-server"
      }
    }
  }
}
```

## 6个工具列表

版本 1.2.8 包含以下6个工具：

1. **get_douyin_download_link** - 获取抖音无水印下载链接
2. **parse_douyin_video_info** - 解析抖音视频基本信息
3. **extract_douyin_text** - 从抖音视频中提取语音转文字（需要 dashscope API）
4. **download_douyin_video** - 下载抖音视频到本地
5. **extract_douyin_audio** - 从抖音视频中提取音频（需要 ffmpeg）
6. **get_video_details** - 获取抖音视频详细信息

## 完整功能依赖

要使用所有功能，需要安装：

```bash
# 基础依赖
pip install douyin-mcp-server1==1.2.8

# 完整功能依赖
pip install douyin-mcp-server1[full]
```

或单独安装：
- `ffmpeg` - 用于视频/音频处理
- `dashscope` - 用于语音转文字
- `ffmpeg-python` - Python ffmpeg 绑定
- `tqdm` - 进度条

## 验证部署

部署后可以通过以下命令验证：

```bash
# 测试工具数量
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | uvx --default-index https://pypi.org/simple douyin-mcp-server1==1.2.8

# 应该返回包含6个工具的响应
```

## 故障排除

如果仍然只有2个工具：
1. 清理 uvx 缓存：`rm -rf ~/.local/share/uv/tools/douyin*`
2. 使用 `--index-url https://pypi.org/simple` 强制使用官方源
3. 检查 Python 路径和权限

如果 "connection closed" 错误：
1. 确保 `DASHSCOPE_API_KEY` 在 `env` 中，不在 `args` 中
2. 检查网络连接
3. 尝试本地安装方式

## 成功标志

成功的部署应该：
- ✅ 显示6个工具
- ✅ 初始化响应正常
- ✅ 没有连接错误
- ✅ 可以调用基础工具（1-2）
- ✅ 高级工具（3-6）会提示需要安装依赖

## 联系支持

如果仍有问题，请提供：
1. 完整的错误日志
2. 使用的方式（uvx/pip/源码）
3. 环境信息（OS/Python版本）