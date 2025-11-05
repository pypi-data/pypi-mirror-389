# MCP 服务器部署指南

## 问题诊断

根据错误日志分析，问题出现在：

1. **uvx 命令执行错误**：当前命令将 `DASHSCOPE_API_KEY` 作为参数传递，而不是环境变量
2. **包版本同步问题**：PyPI镜像可能还没同步到最新版本

## 正确的配置格式

### 配置文件格式 (MCP代理)

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["douyin-mcp-server1==1.2.5"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

**注意**：
- `DASHSCOPE_API_KEY` 必须在 `env` 字段中，不能作为 `args` 传递
- 环境变量名是 `DASHSCOPE_API_KEY`，不是 `dashscope_api_key`

## 解决方案

### 方案1：等待PyPI同步（推荐）

等待几分钟让PyPI镜像完全同步，然后使用正确的配置：

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["douyin-mcp-server1==1.2.5"],
      "env": {
        "DASHSCOPE_API_KEY": "你的实际API密钥"
      }
    }
  }
}
```

### 方案2：使用本地安装

如果急需使用，可以先本地安装：

1. 安装到本地环境：
```bash
pip install douyin-mcp-server1==1.2.4
```

2. 配置使用本地Python：
```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "python",
      "args": ["-m", "douyin_mcp_server1"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥",
        "PYTHONPATH": "/path/to/your/python/site-packages"
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
      "command": "python",
      "args": ["/path/to/douyin-mcp-server/douyin_mcp_server1/mcp_server_simple.py"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥",
        "PYTHONPATH": "/path/to/douyin-mcp-server"
      }
    }
  }
}
```

## 验证部署

部署后可以通过以下方式验证：

```bash
# 测试是否能正确启动
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | uvx douyin-mcp-server1==1.2.5
```

## 常见错误

1. **"connection closed: initialize response"**
   - 通常是因为命令行参数错误
   - 确保 `DASHSCOPE_API_KEY` 在环境变量中

2. **"No solution found when resolving tool dependencies"**
   - PyPI镜像还没同步
   - 可以尝试使用 `--index-url https://pypi.org/simple`

3. **"module not found"**
   - Python路径问题
   - 检查 PYTHONPATH 设置

## 联系支持

如果仍有问题，请提供：
1. 完整的MCP代理配置
2. 错误日志
3. uvx版本 (`uvx --version`)
4. Python版本 (`python --version`)