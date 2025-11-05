#!/usr/bin/env python3
"""
测试代码语法和逻辑
"""
import ast
import sys

# 读取并解析文件
try:
    with open('douyin_mcp_server/server.py', 'r', encoding='utf-8') as f:
        source_code = f.read()

    # 尝试解析 AST
    tree = ast.parse(source_code)
    print("✅ Python 语法检查通过！")

    # 检查关键函数是否存在
    function_names = set()
    class_methods = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            function_names.add(node.name)
            # 检查类方法
            parent = getattr(node, 'parent', None)
            if hasattr(parent, '__class__') and parent.__class__.__name__ == 'ClassDef':
                if hasattr(parent, 'name'):
                    if parent.name not in class_methods:
                        class_methods[parent.name] = []
                    class_methods[parent.name].append(node.name)

    # 检查 DouyinProcessor 类的方法
    if 'DouyinProcessor' in class_methods:
        methods = class_methods['DouyinProcessor']
        required_methods = [
            '__init__',
            'parse_share_url',
            'download_video',
            'extract_audio',
            'get_audio_duration',
            'compress_audio',
            'extract_text_from_audio_file',
            'cleanup_files',
            'cleanup_all'
        ]

        print("\n✅ DouyinProcessor 类检查：")
        for method in required_methods:
            if method in methods:
                print(f"   ✓ {method}")
            else:
                print(f"   ✗ {method} - 缺失！")

    # 检查 MCP 工具函数
    mcp_tools = [name for name in function_names if name.startswith('extract_') or name.startswith('get_') or name.startswith('parse_')]
    print("\n✅ MCP 工具函数：")
    for tool in mcp_tools:
        print(f"   ✓ {tool}")

    # 检查导入语句
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    required_imports = ['os', 'json', 'requests', 'pathlib', 'ffmpeg', 'asyncio', 'dashscope']
    print("\n✅ 导入模块检查：")
    for imp in required_imports:
        if imp in imports:
            print(f"   ✓ {imp}")
        else:
            print(f"   ✗ {imp} - 缺失！")

except SyntaxError as e:
    print(f"✗ 语法错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ 其他错误: {e}")
    sys.exit(1)