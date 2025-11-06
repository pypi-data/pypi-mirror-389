"""
MCP 工具函数
"""
import os
import json
from .processor import DouyinProcessor


def get_douyin_download_link(share_link: str) -> str:
    """
    获取抖音视频的无水印下载链接

    参数:
    - share_link: 抖音分享链接或包含链接的文本

    返回:
    - 包含下载链接和视频信息的JSON字符串
    """
    try:
        processor = DouyinProcessor("")  # 获取下载链接不需要API密钥
        video_info = processor.parse_share_url(share_link)

        return json.dumps({
            "status": "success",
            "video_id": video_info["video_id"],
            "title": video_info["title"],
            "download_url": video_info["url"],
            "description": f"视频标题: {video_info['title']}"
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"获取下载链接失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


def parse_douyin_video_info(share_link: str) -> str:
    """
    解析抖音分享链接，获取视频基本信息

    参数:
    - share_link: 抖音分享链接或包含链接的文本

    返回:
    - 视频信息（JSON格式字符串）
    """
    try:
        processor = DouyinProcessor("")  # 不需要API密钥来解析链接
        video_info = processor.parse_share_url(share_link)

        return json.dumps({
            "video_id": video_info["video_id"],
            "title": video_info["title"],
            "download_url": video_info["url"],
            "status": "success"
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, ensure_ascii=False, indent=2)


async def extract_douyin_text(
    share_link: str,
    model: str = None,
    ctx=None
) -> str:
    """
    从抖音分享链接提取视频中的文本内容

    参数:
    - share_link: 抖音分享链接或包含链接的文本
    - model: 语音识别模型（可选，默认使用paraformer-v2）

    返回:
    - 提取的文本内容

    注意: 需要设置环境变量 DASHSCOPE_API_KEY
    """
    processor = None
    video_path = None
    audio_path = None

    try:
        # 从环境变量获取API密钥
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            raise ValueError("未设置环境变量 DASHSCOPE_API_KEY，请在配置中添加阿里云百炼API密钥")

        processor = DouyinProcessor(api_key, model)

        # 1. 解析视频链接
        if ctx:
            ctx.info("正在解析抖音分享链接...")
        video_info = processor.parse_share_url(share_link)
        if ctx:
            ctx.info(f"视频标题: {video_info['title']}")

        # 2. 下载视频
        if ctx:
            ctx.info("正在下载视频文件...")
        video_path = await processor.download_video(video_info, ctx)

        # 3. 提取音频（使用ffmpeg）
        if ctx:
            ctx.info("正在从视频中提取音频...")
        audio_path = processor.extract_audio(video_path)

        # 4. 从音频文件提取文本
        if ctx:
            ctx.info("正在从音频中提取文本内容...")
        text_content = processor.extract_text_from_audio_file(audio_path, ctx)

        # 5. 清理临时文件
        if ctx:
            ctx.info("正在清理临时文件...")
        if video_path:
            processor.cleanup_files(video_path)
        if audio_path:
            processor.cleanup_files(audio_path)

        if ctx:
            ctx.info("文本提取完成!")
        return text_content

    except Exception as e:
        if ctx:
            ctx.error(f"处理过程中出现错误: {str(e)}")

        # 确保清理文件
        if processor:
            if video_path:
                processor.cleanup_files(video_path)
            if audio_path:
                processor.cleanup_files(audio_path)

        raise Exception(f"提取抖音视频文本失败: {str(e)}")
    finally:
        # 最终清理
        if processor:
            processor.cleanup_all()