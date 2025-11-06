# 部署解决方案

## 问题已解决！

我们通过测试确认：
- ✅ 本地wheel文件可以成功运行
- ❌ PyPI镜像同步存在问题

## 立即可用的解决方案

### 方案1：使用本地wheel文件（已验证可用）

1. **下载wheel文件到您的服务器**：
```bash
# 从我们的服务器下载
wget https://你的服务器地址/douyin_mcp_server1-1.2.5-py3-none-any.whl

# 或者从GitHub下载（如果已发布）
wget https://github.com/yzfly/douyin-mcp-server/releases/download/v1.2.5/douyin_mcp_server1-1.2.5-py3-none-any.whl
```

2. **MCP代理配置**：
```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["/absolute/path/to/douyin_mcp_server1-1.2.5-py3-none-any.whl"],
      "env": {
        "DASHSCOPE_API_KEY": "sk-27ed62f0217240a38efcebff00eeee42"
      }
    }
  }
}
```

**重要**：
- 使用绝对路径
- 确保 `DASHSCOPE_API_KEY` 在 `env` 中，不是 `args` 中

### 方案2：临时HTTP服务器

1. **启动HTTP服务器**（在包含wheel文件的目录）：
```bash
python3 -m http.server 8000
```

2. **配置使用HTTP URL**：
```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["http://你的IP:8000/douyin_mcp_server1-1.2.5-py3-none-any.whl"],
      "env": {
        "DASHSCOPE_API_KEY": "sk-27ed62f0217240a38efcebff00eeee42"
      }
    }
  }
}
```

### 方案3：使用docker

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/path/to/wheel:/app/wheel:ro",
        "python:3.12-slim",
        "bash", "-c",
        "pip install /app/wheel/*.whl && python -m douyin_mcp_server1"
      ],
      "env": {
        "DASHSCOPE_API_KEY": "sk-27ed62f0217240a38efcebff00eeee42"
      }
    }
  }
}
```

## 验证方法

在您的环境中测试：

```bash
# 下载wheel文件
wget https://你的服务器地址/douyin_mcp_server1-1.2.5-py3-none-any.whl

# 测试
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | uvx douyin_mcp_server1-1.2.5-py3-none-any.whl
```

## 为什么这个方案可行

1. **绕过PyPI镜像问题**：直接使用本地文件
2. **保证版本正确**：使用我们测试过的wheel文件
3. **uvx原生支持**：uvx完全支持本地wheel文件安装
4. **环境变量正确**：DASHSCOPE_API_KEY在env中传递

## 长期解决方案

等待PyPI镜像完全同步后，可以改回使用：
```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["--default-index", "https://pypi.org/simple", "douyin-mcp-server1==1.2.5"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

但当前最可靠的方法是使用本地wheel文件。