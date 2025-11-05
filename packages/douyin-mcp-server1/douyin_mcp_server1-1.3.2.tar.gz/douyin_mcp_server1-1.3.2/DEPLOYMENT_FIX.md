# 部署问题修复方案

## 问题诊断

错误 `connection closed: initialize response` 的原因：
1. **PyPI 镜像问题**：uvx 默认使用国内镜像，但 1.2.9 版本还未同步
2. **版本未找到**：uvx 找不到 douyin-mcp-server1==1.2.9

## 解决方案

### 方案1：使用本地 wheel 文件（立即可用）

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

### 方案2：等待 PyPI 同步后使用

几小时后使用：
```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["--index-strategy", "unsafe-best-match", "douyin-mcp-server1==1.2.9"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

### 方案3：直接使用 Python 运行（最稳定）

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

### 方案4：强制使用官方源

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": [
        "--index-url", "https://pypi.org/simple",
        "--index-strategy", "unsafe-best-match",
        "douyin-mcp-server1==1.2.9"
      ],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

## 验证方法

测试是否有6个工具：
```bash
# 使用本地 wheel
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | uvx /app/test/douyin-mcp-server/dist/douyin_mcp_server1-1.2.9-py3-none-any.whl

# 或直接运行
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 -m douyin_mcp_server1.mcp_server_simple
```

## 核心问题

1. **uvx 镜像同步延迟**：新版本需要时间同步到所有镜像
2. **connection closed**：通常是版本不匹配或找不到包导致的

## 临时解决措施

如果急需使用，建议：
1. 下载本地 wheel 文件使用
2. 或直接用 Python 运行源码
3. 等待几小时后 PyPI 完全同步再使用 uvx