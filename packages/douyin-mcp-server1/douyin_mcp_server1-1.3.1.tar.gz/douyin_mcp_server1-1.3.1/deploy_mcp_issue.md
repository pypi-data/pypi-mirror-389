# MCP 部署失败原因分析

## 问题定位

从日志看到：
```
完整命令字符串: uvx --default-index https://pypi.org/simple douyin-mcp-server1==1.3.0 DASHSCOPE_API_KEY=sk-27ed62f0217240a38efcebff00eeee42
```

**核心问题**：环境变量 `DASHSCOPE_API_KEY` 被错误地当作命令行参数传递了！

## MCP 开发规范

MCP 服务器必须：
1. 通过 stdin/stdout 进行 JSON-RPC 通信
2. 环境变量通过 `env` 字段传递，不是命令行参数
3. 不能直接输出到 stdout（会干扰 JSON-RPC）

## 根本原因

MCP 代理程序（mcp_proxy）错误地将环境变量作为命令行参数传递，导致：
1. `uvx` 收到意外的参数 `DASHSCOPE_API_KEY=...`
2. 参数解析错误
3. uvx 无法正确启动
4. 连接断开

## 解决方案

### 方案1：修复 MCP 代理配置

MCP 代理需要正确处理环境变量：

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["--default-index", "https://pypi.org/simple", "douyin-mcp-server1==1.3.0"],
      "env": {
        "DASHSCOPE_API_KEY": "sk-27ed62f0217240a38efcebff00eeee42"
      }
    }
  }
}
```

`env` 必须作为独立字段，不能和 `args` 混淆！

### 方案2：使用 Python 直接运行（避免 uvx）

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "python3",
      "args": ["-m", "douyin_mcp_server1"],
      "env": {
        "DASHSCOPE_API_KEY": "sk-27ed62f0217240a38efcebff00eeee42"
      }
    }
  }
}
```

### 方案3：创建启动脚本

创建 `start_mcp.sh`：
```bash
#!/bin/bash
export DASHSCOPE_API_KEY="$DASHSCOPE_API_KEY"
exec python3 -m douyin_mcp_server1
```

然后配置：
```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "/path/to/start_mcp.sh",
      "args": []
    }
  }
}
```

## 测试验证

手动测试：
```bash
# 正确的方式
export DASHSCOPE_API_KEY=sk-27ed62f0217240a38efcebff00eeee42
uvx --default-index https://pypi.org/simple douyin-mcp-server1==1.3.0

# 错误的方式（会导致失败）
uvx --default-index https://pypi.org/simple douyin-mcp-server1==1.3.0 DASHSCOPE_API_KEY=sk-27ed62f0217240a38efcebff00eeee42
```

## 结论

这不是 MCP 服务器代码的问题，而是：
1. **MCP 代理没有正确处理环境变量**
2. **环境变量被错误地作为命令行参数传递**

需要修复 MCP 代理的实现，确保：
- `args` 只包含命令行参数
- `env` 作为独立字段传递给子进程的环境