# MCP 服务器部署修复方案 - 版本 1.3.1

## 修复内容

### 1. 支持多种参数传递方式
MCP 服务器现在支持：
- 标准环境变量传递
- 命令行参数格式：`DASHSCOPE_API_KEY=xxx`
- 混合参数传递（uvx 风格）

### 2. 符合 MCP 规范
- 只通过 stdout 输出 JSON-RPC 响应
- 调试信息输出到 stderr
- 支持标准 JSON-RPC 2.0 协议
- 正确错误处理

## 部署配置

### 方案1：使用 uvx（支持参数混合）
```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "uvx",
      "args": ["--index-url", "https://pypi.org/simple", "douyin-mcp-server1==1.3.1"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥"
      }
    }
  }
}
```

即使环境变量被错误地当作命令行参数传递，服务器也能正常处理。

### 方案2：直接运行 Python
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

### 方案3：带调试信息
```json
{
  "mcpServers": {
    "douyin-mcp1": {
      "command": "python3",
      "args": ["-m", "douyin_mcp_server1"],
      "env": {
        "DASHSCOPE_API_KEY": "你的API密钥",
        "MCP_DEBUG": "1"
      }
    }
  }
}
```

## 验证测试

```bash
# 测试工具数量
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 -m douyin_mcp_server1

# 测试环境变量参数
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"extract_douyin_text","arguments":{"share_link":"test"}}}' | python3 -m douyin_mcp_server1 DASHSCOPE_API_KEY=test123

# 测试混合参数
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}}}}' | python3 -m douyin_mcp_server1 --param value DASHSCOPE_API_KEY=test123
```

## 关键改进

1. **自动处理命令行环境变量**：
   ```python
   for arg in sys.argv[1:]:
       if '=' in arg and not arg.startswith('-'):
           key, value = arg.split('=', 1)
           os.environ[key] = value
   ```

2. **错误处理改进**：
   - JSON 解析错误静默跳过
   - 返回标准错误响应
   - 调试信息输出到 stderr

3. **支持 `-m` 执行**：
   - 添加了 `__main__.py`
   - 支持 `python -m douyin_mcp_server1`

## 核心文件

```
douyin_mcp_server1/
├── __init__.py         # 主入口（包含所有6个工具）
├── __main__.py         # 支持 -m 执行
├── tools.py           # 基础工具
├── processor.py       # 高级处理器
└── server.py          # 完整版（可选）
```

## 6个工具列表

1. get_douyin_download_link - 获取无水印链接
2. parse_douyin_video_info - 解析视频信息
3. extract_douyin_text - 语音转文字
4. download_douyin_video - 下载视频
5. extract_douyin_audio - 提取音频
6. get_video_details - 视频详情

现在服务器能够灵活处理各种部署场景，即使 MCP 代理没有正确传递环境变量也能正常工作。