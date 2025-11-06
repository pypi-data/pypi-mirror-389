# MCP 部署修复方案

## 问题诊断

**错误原因**：MCP 代理将环境变量错误地作为命令行参数传递

```
错误: uvx --default-index https://pypi.org/simple douyin-mcp-server1==1.3.0 DASHSCOPE_API_KEY=sk-xxx
正确: uvx --default-index https://pypi.org/simple douyin-mcp-server1==1.3.0
      (DASHSCOPE_API_KEY 应该在环境变量中)
```

## 立即解决方案

### 方案1：使用 Python 直接运行（推荐）

```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "python3",
      "args": ["-m", "douyin_mcp_server1"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

### 方案2：使用包装脚本

1. 下载 `douyin_mcp_wrapper.sh`：
```bash
#!/bin/bash
exec python3 -m douyin_mcp_server1
```

2. 配置：
```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "/path/to/douyin_mcp_wrapper.sh",
      "args": [],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

### 方案3：本地安装后运行

```bash
# 先安装
pip install douyin-mcp-server1==1.3.0

# 然后使用
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "douyin-mcp-server1",
      "args": [],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

## 测试部署

验证命令：
```bash
# 应该返回6个工具
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 -m douyin_mcp_server1
```

## MCP 开发规范说明

1. **JSON-RPC 通信**：通过 stdin/stdout
2. **环境变量**：必须通过环境传递，不能作为命令行参数
3. **无调试输出**：不能向 stdout 输出非 JSON 内容
4. **错误处理**：返回标准的 JSON-RPC 错误格式

## 关键点

- **这不是代码问题**，是部署配置问题
- **环境变量必须独立于 args**
- uvx 本身没问题，是参数传递方式错误