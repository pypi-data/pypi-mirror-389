#!/usr/bin/env python3
"""
抖音无水印链接提取 MCP 服务器 - 使用 FastMCP
完全按照原版结构
"""

import re
import json
import os

# 使用真正的 FastMCP
from fastmcp import FastMCP

# 按照原版创建 MCP 服务器实例
mcp = FastMCP("Douyin Link Extractor")

# 请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 Version/17.0 Mobile/15E148 Safari/604.1'
}


def parse_share_url(share_text: str):
    """从分享文本中提取无水印视频链接 - 完全按照原版实现"""
    try:
        import requests

        # 提取分享链接 - 按照原版，修复URL截断问题
        share_url = None
        # 尝试多种模式匹配完整的URL
        patterns = [
            r'https?://v\.douyin\.com/[A-Za-z0-9]+',  # 最常见的模式
            r'https?://www\.iesdouyin\.com/share/video/\d+',  # 完整分享页面
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$\-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # 通用模式
        ]

        for pattern in patterns:
            matches = re.findall(pattern, share_text)
            if matches:
                share_url = matches[0]
                break

        if not share_url:
            raise Exception("未找到有效的分享链接")

        # 获取分享链接的响应，获取重定向后的URL提取video_id
        share_response = requests.get(share_url, headers=headers, allow_redirects=True)
        video_id = share_response.url.split("?")[0].strip("/").split("/")[-1]

        # 构造抖音分享页面URL - 按照原版
        share_url = f'https://www.iesdouyin.com/share/video/{video_id}'

        # 获取视频页面内容 - 按照原版
        response = requests.get(share_url, headers=headers)
        response.raise_for_status()
        pattern = re.compile(
            pattern=r"window\._ROUTER_DATA\s*=\s*(.*?)</script>",
            flags=re.DOTALL,
        )

        find_res = pattern.search(response.text)

        if not find_res or not find_res.group(1):
            # 如果解析失败，返回基本信息
            return {
                "url": f"https://download.douyin.com/video/{video_id}",
                "title": f"douyin_{video_id}",
                "video_id": video_id,
                "error": "从HTML中解析视频信息失败"
            }

        # 解析JSON数据 - 按照原版
        json_data = json.loads(find_res.group(1).strip())
        VIDEO_ID_PAGE_KEY = "video_(id)/page"
        NOTE_ID_PAGE_KEY = "note_(id)/page"

        if VIDEO_ID_PAGE_KEY in json_data["loaderData"]:
            original_video_info = json_data["loaderData"][VIDEO_ID_PAGE_KEY]["videoInfoRes"]
        elif NOTE_ID_PAGE_KEY in json_data["loaderData"]:
            original_video_info = json_data["loaderData"][NOTE_ID_PAGE_KEY]["videoInfoRes"]
        else:
            # 如果找不到数据，返回基本信息
            return {
                "url": f"https://download.douyin.com/video/{video_id}",
                "title": f"douyin_{video_id}",
                "video_id": video_id,
                "error": "无法从JSON中解析视频或图集信息"
            }

        data = original_video_info["item_list"][0]

        # 获取视频信息 - 按照原版
        video_url = data["video"]["play_addr"]["url_list"][0].replace("playwm", "play")
        desc = data.get("desc", "").strip() or f"douyin_{video_id}"

        # 替换文件名中的非法字符
        desc = re.sub(r'[\\/:*?"<>|]', '_', desc)

        return {
            "url": video_url,
            "title": desc,
            "video_id": video_id
        }

    except Exception as e:
        # 出错时尝试至少提取video_id
        try:
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', share_text)
            if urls:
                share_response = requests.get(urls[0], headers=headers, allow_redirects=True)
                video_id = share_response.url.split("?")[0].strip("/").split("/")[-1]
            else:
                video_id = "unknown"
        except:
            video_id = "unknown"

        return {
            "url": f"https://download.douyin.com/video/{video_id}",
            "title": f"douyin_{video_id}",
            "video_id": video_id,
            "error": str(e)
        }


# 完全按照原版定义工具 - 使用装饰器
@mcp.tool()
def get_douyin_video_url(share_text: str) -> str:
    """
    从抖音分享文本中提取无水印视频链接

    Args:
        share_text: 包含抖音分享链接的文本

    Returns:
        无水印视频下载链接
    """
    try:
        result = parse_share_url(share_text)
        return result["url"]
    except Exception as e:
        return f"错误：{str(e)}"


@mcp.tool()
def get_douyin_download_link(share_text: str) -> str:
    """
    获取抖音视频的无水印下载链接

    Args:
        share_text: 包含抖音分享链接的文本

    Returns:
        JSON格式的下载链接信息
    """
    try:
        result = parse_share_url(share_text)
        return json.dumps({
            "status": "success",
            "download_url": result["url"],
            "title": result["title"],
            "video_id": result["video_id"]
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False)


@mcp.tool()
def parse_douyin_video_info(share_text: str) -> str:
    """
    解析抖音视频基本信息

    Args:
        share_text: 包含抖音分享链接的文本

    Returns:
        JSON格式的视频信息
    """
    try:
        result = parse_share_url(share_text)
        return json.dumps({
            "status": "success",
            "video_id": result["video_id"],
            "title": result["title"],
            "share_link": share_text
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False)


@mcp.tool()
def extract_douyin_text(share_text: str, model: str = "paraformer-realtime-v1") -> str:
    """
    从抖音视频中提取语音转文字

    Args:
        share_text: 包含抖音分享链接的文本
        model: 使用的语音识别模型

    Returns:
        JSON格式的提取结果
    """
    import sys
    import tempfile
    import subprocess
    import os
    from pathlib import Path

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return json.dumps({
            "status": "error",
            "message": "需要设置 DASHSCOPE_API_KEY 环境变量",
            "share_link": share_text
        }, ensure_ascii=False)

    try:
        # 导入依赖
        import dashscope
        from dashscope.audio.asr import Transcription
        import requests
        import ffmpeg

        # 获取视频链接
        result = parse_share_url(share_text)
        video_url = result.get("url")
        video_id = result.get("video_id")
        error = result.get("error")

        # 如果有错误，返回错误信息
        if error:
            return json.dumps({
                "status": "error",
                "message": f"解析失败: {error}",
                "extracted_text": "",
                "share_link": share_text,
                "video_id": video_id,
                "model": model,
                "note": "请检查抖音分享链接是否有效"
            }, ensure_ascii=False)

        # 创建临时目录（使用进程ID避免冲突）
        temp_dir = tempfile.mkdtemp(prefix=f"douyin_{os.getpid()}_")
        video_path = os.path.join(temp_dir, "video.mp4")
        audio_path = os.path.join(temp_dir, "audio.wav")

        try:
            # 下载视频
            response = requests.get(video_url, headers=headers, stream=True)
            response.raise_for_status()

            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 提取音频为WAV格式（Dashscope API支持WAV）
            (
                ffmpeg
                .input(video_path)
                .output(audio_path, acodec='pcm_s16le', ar='16000', ac=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            # 检查音频文件是否存在
            if not os.path.exists(audio_path):
                raise Exception(f"音频文件未生成: {audio_path}")

            # 检查音频文件大小
            audio_size = os.path.getsize(audio_path)
            if audio_size == 0:
                raise Exception(f"音频文件为空: {audio_path}")

            print(f"[DEBUG] 音频文件: {audio_path}, 大小: {audio_size/1024:.2f}KB")

            # 验证音频文件是否有效
            try:
                # 使用ffprobe验证音频文件
                cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', audio_path]
                probe_result = subprocess.run(cmd, capture_output=True, text=True)
                if probe_result.returncode == 0 and probe_result.stdout.strip():
                    duration = float(probe_result.stdout.strip())
                    print(f"[DEBUG] 音频时长: {duration:.2f}秒")
                else:
                    print(f"[DEBUG] 音频文件可能损坏: {probe_result.stderr}")
            except Exception as e:
                print(f"[DEBUG] 无法验证音频文件: {e}")

            if audio_size > 50 * 1024 * 1024:  # 50MB
                # WAV文件无法有效压缩，返回错误
                return json.dumps({
                    "status": "error",
                    "message": f"音频文件过大 ({audio_size/1024/1024:.2f}MB)，超过50MB限制",
                    "share_link": share_text,
                    "model": model,
                    "note": "请尝试较短的音视频"
                }, ensure_ascii=False)

            # 调用 Dashscope API
            dashscope.api_key = api_key

            # 使用正确的 Dashscope API 调用方式
            transcription = Transcription()

            # 使用绝对路径（根据processor.py的成功案例）
            file_path = os.path.abspath(audio_path)
            print(f"[DEBUG] 提交给API的文件路径: {file_path}")

            result = transcription.async_call(
                model=model,
                file_urls=[file_path],  # 使用绝对路径，不加file://前缀
                language_hints=["zh", "zh-CN", "en"],
                formats=["txt"]
            )

            # 更详细的错误处理
            print(f"[DEBUG] API返回状态码: {result.status_code}")
            print(f"[DEBUG] API请求ID: {getattr(result, 'request_id', 'N/A')}")

            if hasattr(result, 'message'):
                print(f"[DEBUG] API错误消息: {result.message}")

            if hasattr(result, 'output') and result.output:
                print(f"[DEBUG] API输出: {result.output}")

            # 打印完整的结果对象
            import pprint
            print(f"[DEBUG] 完整API响应:")
            pprint.pprint(vars(result))

            if result.status_code == '200' and result.output:
                text = result.output['transcript_result']['text']

                return json.dumps({
                    "status": "success",
                    "message": "语音提取成功",
                    "extracted_text": text,
                    "share_link": share_text,
                    "model": model,
                    "audio_size": f"{os.path.getsize(audio_path)/1024/1024:.2f}MB"
                }, ensure_ascii=False)
            else:
                # 收集更详细的错误信息
                error_msg = getattr(result, 'message', '未知错误')
                if hasattr(result, 'output') and result.output:
                    error_msg += f" | 输出: {result.output}"

                return json.dumps({
                    "status": "error",
                    "message": f"语音识别失败: {error_msg}",
                    "share_link": share_text,
                    "model": model,
                    "debug_info": {
                        "status_code": result.status_code,
                        "file_path": file_path,
                        "file_exists": os.path.exists(file_path),
                        "file_size": f"{os.path.getsize(file_path)/1024:.2f}KB" if os.path.exists(file_path) else "N/A"
                    }
                }, ensure_ascii=False)

        finally:
            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    except ImportError as e:
        missing_pkg = str(e).split("'")[1] if "'" in str(e) else str(e)
        return json.dumps({
            "status": "error",
            "message": f"缺少依赖包: {missing_pkg}",
            "share_link": share_text,
            "note": "请确保已安装所有依赖: pip install dashscope ffmpeg-python"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"处理过程中出错: {str(e)}",
            "share_link": share_text,
            "model": model
        }, ensure_ascii=False)


@mcp.tool()
def download_douyin_video(share_text: str, output_dir: str = "./downloads") -> str:
    """
    下载抖音视频到本地

    Args:
        share_text: 包含抖音分享链接的文本
        output_dir: 输出目录路径

    Returns:
        JSON格式的下载结果
    """
    # 简化实现
    return json.dumps({
        "status": "info",
        "message": "视频下载功能需要完整版依赖",
        "share_link": share_text,
        "output_dir": output_dir,
        "note": "请安装: pip install douyin-mcp-server1[full]"
    }, ensure_ascii=False)


@mcp.tool()
def extract_audio_from_local_file(file_path: str, model: str = "paraformer-realtime-v1") -> str:
    """
    从本地视频文件中提取语音转文字

    Args:
        file_path: 本地视频文件的绝对路径
        model: 使用的语音识别模型

    Returns:
        JSON格式的提取结果
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return json.dumps({
            "status": "error",
            "message": "需要设置 DASHSCOPE_API_KEY 环境变量",
            "file_path": file_path
        }, ensure_ascii=False)

    try:
        # 导入本地处理模块
        import sys
        import importlib.util
        spec = importlib.util.spec_from_file_location("extract_local_video", os.path.join(os.path.dirname(__file__), "extract_local_video.py"))
        extract_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(extract_module)

        # 处理视频文件
        result = extract_module.process_video_file(file_path, api_key, model)

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"处理失败: {str(e)}",
            "file_path": file_path,
            "note": "请确保文件路径正确且格式支持"
        }, ensure_ascii=False)


@mcp.tool()
def get_video_details(share_text: str) -> str:
    """
    获取抖音视频详细信息

    Args:
        share_text: 包含抖音分享链接的文本

    Returns:
        JSON格式的详细信息
    """
    try:
        result = parse_share_url(share_text)
        return json.dumps({
            "status": "success",
            "video_id": result["video_id"],
            "title": result["title"],
            "download_url": result["url"],
            "share_link": share_text,
            "timestamp": str(int(__import__("time").time()))
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False)


def main():
    """主函数 - 完全按照原版"""
    # FastMCP会自动处理所有事情，不显示banner
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()