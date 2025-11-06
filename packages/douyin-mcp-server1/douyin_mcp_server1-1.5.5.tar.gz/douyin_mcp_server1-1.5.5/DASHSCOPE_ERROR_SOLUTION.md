# Dashscope API 错误解决方案

## 问题描述

错误信息：`Transcription.async_call() missing 1 required positional argument: 'file_urls'`

## 问题原因

`dashscope` SDK 的 API 已经更新，不再接受 `file` 参数，而是需要 `file_urls` 参数。

## 解决方案

### 方案1：修复现有代码（推荐）

我已经修复了 `processor.py` 中的问题，将：
```python
file=[audio_file]
```
改为：
```python
file_urls=[str(compressed_audio)]
```

### 方案2：使用 mcp_server_simple.py（不依赖dashscope）

当前部署的 mcp_server_simple.py 不包含语音转文本功能，只有基础的下载和解析功能。这可以避免 dashscope 相关的错误。

### 方案3：完全修复并重新发布

如果要保留语音转文本功能，需要：

1. **修复所有相关文件**：
   - ✅ processor.py（已修复）
   - ❌ server.py（需要修复）

2. **重新构建和发布**：
   ```bash
   # 更新版本号
   version="1.2.6"

   # 重新构建
   python -m build

   # 上传新版本
   python -m twine upload dist/*.whl *.tar.gz
   ```

### 方案4：使用不同的语音识别服务

如果 dashscope 问题持续，可以考虑：
- 使用 OpenAI Whisper API
- 使用本地 Whisper 模型
- 使用其他语音识别服务

## 临时解决方案

如果急需使用，可以：

1. **禁用语音转文本功能**：
   ```json
   {
     "mcpServers": {
       "douyin-mcp1": {
         "command": "uvx",
         "args": ["/path/to/douyin_mcp_server1-1.2.5-py3-none-any.whl"],
         "env": {
           "DASHSCOPE_API_KEY": "你的密钥",
           "DISABLE_TRANSCRIPTION": "true"
         }
       }
     }
   }
   ```

2. **只使用基础功能**：
   - `get_douyin_download_link` - 获取下载链接
   - `parse_douyin_video_info` - 解析视频信息

## 建议的步骤

1. **立即可用**：使用当前的 mcp_server_simple.py 版本（不包含语音转文本）
2. **如果需要语音转文本**：等待修复版本 1.2.6 发布
3. **或使用其他语音识别方案**

## 代码修复示例

正确的 dashscope 调用方式：

```python
import dashscope
from dashscope import Audio

# 正确的方式 - 使用文件路径
task_response = Audio.async_call(
    model='paraformer-realtime-v1',
    file_urls=['/path/to/audio.wav'],  # 完整路径
    language_hints=['zh', 'en']
)

# 等待结果
result = Audio.wait(task=task_response.output.task_id)
```

## 相关文档

- [Dashscope 音频转写文档](https://help.aliyun.com/zh/dashscope/developer-reference/quick-start)
- [MCP 协议文档](https://modelcontextprotocol.io/)