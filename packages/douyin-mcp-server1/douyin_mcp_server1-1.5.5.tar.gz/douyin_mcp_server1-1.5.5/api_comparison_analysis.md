# API调用方式对比分析

## 原项目 vs 当前实现

### 1. 音频格式差异

**原项目 processor.py**:
- 使用 MP3 格式: `video_path.with_suffix('.mp3')`
- 编码器: `acodec='libmp3lame'`
- 高质量设置: `q=0, ar='44100', ac=2`
- 压缩后也是MP3: `audio_path.with_suffix('.compressed.mp3')`

**当前实现**:
- 使用 WAV 格式: `audio.wav`
- 编码器: `acodec='pcm_s16le'`
- 低质量设置: `ar='16000', ac=1`
- 无法压缩（WAV文件太大）

### 2. API调用方式差异

**原项目**:
```python
# 1. 先创建转录任务
task_response = dashscope.audio.asr.Transcription.async_call(
    model=self.model,
    file_urls=[str(compressed_audio)],  # 普通路径
    language_hints=['zh', 'en']
)

# 2. 然后等待任务完成
transcription_response = dashscope.audio.asr.Transcription.wait(
    task=task_response.output.task_id
)

# 3. 获取结果
url = transcription_response.output['results'][0]['transcription_url']
result = json.loads(request.urlopen(url).read().decode('utf8'))
text = result['transcripts'][0]['text']
```

**当前实现**:
```python
# 1. 直接调用并等待结果
result = transcription.async_call(
    model=model,
    file_urls=[file_uri],  # file:// URI
    language_hints=["zh", "zh-CN", "en"],
    formats=["txt"]
)

# 2. 直接从结果获取
text = result.output['transcript_result']['text']
```

### 3. 关键问题分析

1. **FFmpeg缺少libmp3lame编码器**
   - 原项目依赖MP3格式
   - 当前环境无法生成MP3

2. **API调用流程不同**
   - 原项目: async_call + wait
   - 当前实现: 直接async_call

3. **响应处理方式不同**
   - 原项目: 从transcription_url获取结果
   - 当前实现: 直接从output获取

### 解决方案

由于FFmpeg缺少libmp3lame，需要：

1. **使用WAV格式但调整API调用方式**
   - 采用原项目的两步调用方式
   - async_call + wait

2. **或者安装MP3编码器**
   - apt-get install libavcodec-extra

### 错误原因
"url error" 可能是因为：
1. Dashscope API版本差异
2. 调用方式不正确（缺少wait步骤）
3. 响应处理方式错误