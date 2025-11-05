#!/usr/bin/env python3
"""
测试代码逻辑（不需要导入 ffmpeg）
"""
import inspect
import sys
import os

# 模拟缺失的模块
class MockFFmpeg:
    def input(self, *args, **kwargs):
        return self
    def output(self, *args, **kwargs):
        return self
    def run(self, *args, **kwargs):
        return None
    def __getattr__(self, name):
        return self

class MockDashscope:
    class audio:
        class asr:
            class Transcription:
                @staticmethod
                def async_call(**kwargs):
                    class MockResponse:
                        output = type('obj', (object,), {'task_id': 'mock_task_id'})
                    return MockResponse()

                @staticmethod
                def wait(task):
                    class MockResponse:
                        status_code = 200
                        output = {
                            'results': [{
                                'transcription_url': 'http://mock.url'
                            }]
                        }
                    return MockResponse()

    api_key = None

# 注入模拟模块
sys.modules['ffmpeg'] = MockFFmpeg()
sys.modules['dashscope'] = MockDashscope()
sys.modules['tqdm.asyncio'] = type('module', (), {'tqdm': lambda x: x})()
sys.modules['mcp.server.fastmcp'] = type('module', (), {
    'FastMCP': lambda *args, **kwargs: type('MCP', (), {})(),
    'Context': type('Context', (), {
        'info': lambda self, x: print(f"[INFO] {x}"),
        'error': lambda self, x: print(f"[ERROR] {x}"),
        'report_progress': lambda self, a, b: None
    })()
})()

try:
    # 导入主模块
    from douyin_mcp_server.server import DouyinProcessor, extract_douyin_text

    print("✅ 代码导入成功！")

    # 检查 DouyinProcessor 类实例化
    print("\n✅ 测试 DouyinProcessor 初始化...")
    processor = DouyinProcessor(api_key="test_key", model="test_model")
    print(f"   进程ID: {processor.process_id}")
    print(f"   唯一ID: {processor.unique_id}")
    print(f"   临时目录: {processor.temp_dir}")
    print(f"   ✓ 初始化成功！")

    # 检查方法签名
    print("\n✅ 检查方法签名...")

    # 检查 extract_douyin_text
    sig = inspect.signature(extract_douyin_text)
    params = list(sig.parameters.keys())
    print(f"   extract_douyin_text 参数: {params}")

    # 检查 compress_audio 方法
    sig = inspect.signature(processor.compress_audio)
    params = list(sig.parameters.keys())
    print(f"   compress_audio 参数: {params}")

    # 检查 extract_text_from_audio_file 方法
    sig = inspect.signature(processor.extract_text_from_audio_file)
    params = list(sig.parameters.keys())
    print(f"   extract_text_from_audio_file 参数: {params}")

    print("\n✅ 所有测试通过！代码结构正确。")

except ImportError as e:
    print(f"✗ 导入错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ 运行错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)