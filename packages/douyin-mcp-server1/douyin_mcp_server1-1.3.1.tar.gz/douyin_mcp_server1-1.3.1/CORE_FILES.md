# 核心文件结构

## 清理后的项目结构

```
douyin-mcp-server/
├── douyin_mcp_server1/          # 主模块
│   ├── __init__.py              # 核心入口 - 包含所有6个工具和主函数
│   ├── tools.py                 # 工具函数（供processor使用）
│   ├── processor.py             # 高级处理器（视频下载、音频处理）
│   └── server.py                # 完整版服务器（使用FastMCP）
├── pyproject.toml               # 项目配置和依赖
├── README.md                    # 项目说明
├── LICENSE                      # 许可证
└── dist/                        # 构建输出
```

## 核心文件说明

### 1. `__init__.py` (主入口)
- **功能**：MCP服务器的主要入口点
- **包含**：
  - 6个工具的定义和处理逻辑
  - JSON-RPC请求处理
  - main() 函数
- **特点**：无外部依赖，只需要 mcp 和 requests

### 2. `tools.py`
- **功能**：基础工具函数
- **包含**：获取下载链接、解析视频信息等

### 3. `processor.py`
- **功能**：高级功能处理器
- **包含**：
  - 视频下载
  - 音频提取和压缩
  - Dashscope API调用
- **依赖**：ffmpeg, dashscope, tqdm

### 4. `server.py`
- **功能**：完整版服务器实现
- **特点**：使用FastMCP框架
- **依赖**：fastmcp等

## 部署入口

pyproject.toml 配置：
```toml
[project.scripts]
douyin-mcp-server1 = "douyin_mcp_server1:main"
```

## 使用方式

1. **基础版**（2个工具）：直接使用 __init__.py
2. **完整版**（6个工具）：需要安装额外依赖 [full]

## 已删除的文件

- 所有 mcp_server_*.py（重复的server实现）
- 所有测试文件（*.py）
- 所有临时构建文件
- __main__.py

现在项目结构清晰，只保留核心功能文件。