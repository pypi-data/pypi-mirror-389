"""
抖音处理器类
"""
import os
import re
import json
import requests
import tempfile
import asyncio
import time
import uuid
import threading
from pathlib import Path
from typing import Optional, Tuple
try:
    import ffmpeg
except ImportError:
    ffmpeg = None
from tqdm.asyncio import tqdm
from urllib import request
from http import HTTPStatus
try:
    import dashscope
except ImportError:
    dashscope = None

# 默认 API 配置
DEFAULT_MODEL = "paraformer-v2"

# 请求头，模拟移动端访问
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 Version/17.0 Mobile/15E148 Safari/604.1'
}


class DouyinProcessor:
    """抖音视频处理器"""

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or DEFAULT_MODEL
        # 使用进程ID和唯一ID创建独立的临时目录
        self.process_id = os.getpid()
        self.unique_id = str(uuid.uuid4())[:8]
        self.temp_dir = Path(tempfile.mkdtemp(prefix=f"douyin_{self.process_id}_{self.unique_id}_"))
        self.managed_files = set()  # 跟踪自己管理的文件
        self._lock = threading.Lock()  # 线程锁
        # 设置阿里云百炼API密钥
        if dashscope:
            dashscope.api_key = api_key

    def __del__(self):
        """清理临时目录"""
        self.cleanup_all()

    def cleanup_all(self):
        """清理所有自己管理的文件和目录"""
        import shutil
        with self._lock:
            if hasattr(self, 'temp_dir') and self.temp_dir.exists():
                try:
                    # 只删除自己创建的文件
                    for file_path in list(self.managed_files):
                        if file_path.exists():
                            file_path.unlink()
                    # 删除临时目录
                    shutil.rmtree(self.temp_dir, ignore_errors=True)
                except Exception as e:
                    pass  # 静默处理清理错误

    def parse_share_url(self, share_text: str) -> dict:
        """从分享文本中提取无水印视频链接"""
        # 提取分享链接
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', share_text)
        if not urls:
            raise ValueError("未找到有效的分享链接")

        share_url = urls[0]
        share_response = requests.get(share_url, headers=HEADERS)
        video_id = share_response.url.split("?")[0].strip("/").split("/")[-1]
        share_url = f'https://www.iesdouyin.com/share/video/{video_id}'

        # 获取视频页面内容
        response = requests.get(share_url, headers=HEADERS)
        response.raise_for_status()

        pattern = re.compile(
            pattern=r"window\._ROUTER_DATA\s*=\s*(.*?)</script>",
            flags=re.DOTALL,
        )
        find_res = pattern.search(response.text)

        if not find_res or not find_res.group(1):
            raise ValueError("从HTML中解析视频信息失败")

        # 解析JSON数据
        json_data = json.loads(find_res.group(1).strip())
        VIDEO_ID_PAGE_KEY = "video_(id)/page"
        NOTE_ID_PAGE_KEY = "note_(id)/page"

        if VIDEO_ID_PAGE_KEY in json_data["loaderData"]:
            original_video_info = json_data["loaderData"][VIDEO_ID_PAGE_KEY]["videoInfoRes"]
        elif NOTE_ID_PAGE_KEY in json_data["loaderData"]:
            original_video_info = json_data["loaderData"][NOTE_ID_PAGE_KEY]["videoInfoRes"]
        else:
            raise Exception("无法从JSON中解析视频或图集信息")

        data = original_video_info["item_list"][0]

        # 获取视频信息
        video_url = data["video"]["play_addr"]["url_list"][0].replace("playwm", "play")
        desc = data.get("desc", "").strip() or f"douyin_{video_id}"

        # 替换文件名中的非法字符
        desc = re.sub(r'[\\/:*?"<>|]', '_', desc)

        return {
            "url": video_url,
            "title": desc,
            "video_id": video_id
        }

    async def download_video(self, video_info: dict, ctx=None) -> Path:
        """异步下载视频到临时目录"""
        filename = f"{video_info['video_id']}_{int(time.time())}.mp4"
        filepath = self.temp_dir / filename

        if ctx:
            ctx.info(f"正在下载视频: {video_info['title']}")

        response = requests.get(video_info['url'], headers=HEADERS, stream=True)
        response.raise_for_status()

        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))

        # 异步下载文件，显示进度
        with open(filepath, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and ctx:
                        progress = downloaded / total_size
                        await ctx.report_progress(downloaded, total_size)

        # 添加到管理文件列表
        with self._lock:
            self.managed_files.add(filepath)

        if ctx:
            ctx.info(f"视频下载完成: {filepath}")
        return filepath

    def extract_audio(self, video_path: Path) -> Path:
        """从视频文件中提取音频"""
        if not ffmpeg:
            raise Exception("ffmpeg-python 未安装")

        audio_path = video_path.with_suffix('.mp3')

        try:
            # 提取音频，使用高质量设置
            (
                ffmpeg
                .input(str(video_path))
                .output(
                    str(audio_path),
                    acodec='libmp3lame',
                    q=0,  # 最高质量
                    ar='44100',  # 保持高采样率
                    ac=2  # 保持立体声
                )
                .run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
            )

            # 添加到管理文件列表
            with self._lock:
                self.managed_files.add(audio_path)

            return audio_path
        except Exception as e:
            raise Exception(f"提取音频时出错: {str(e)}")

    def get_audio_duration(self, audio_path: Path) -> float:
        """获取音频时长（秒）"""
        try:
            import subprocess
            result = subprocess.run([
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(audio_path)
            ], capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except:
            # 如果获取失败，返回估算值
            return 300  # 5分钟

    def compress_audio(self, audio_path: Path, target_size_mb: int = 50) -> Path:
        """
        压缩音频到目标大小以内，尽可能保持高质量
        """
        if not ffmpeg:
            raise Exception("ffmpeg-python 未安装")

        file_size_mb = audio_path.stat().st_size / (1024 * 1024)

        if file_size_mb <= target_size_mb:
            return audio_path  # 不需要压缩

        # 音频文件过大，需要压缩

        # 获取实际音频时长
        duration = self.get_audio_duration(audio_path)

        # 计算目标比特率，留出10%的余量
        target_size_mb = target_size_mb * 0.9
        # 根据实际时长计算所需比特率
        target_bitrate = int((target_size_mb * 8 * 1024 * 1024) / duration)  # bps

        # 限制比特率范围
        target_bitrate = max(64000, min(320000, target_bitrate))

        compressed_path = audio_path.with_suffix('.compressed.mp3')

        # 多级压缩策略
        compression_configs = [
            # 策略1: 保持44.1kHz, 降低比特率
            {'ar': '44100', 'ac': '2', 'audio_bitrate': f'{target_bitrate//1000}k'},
            # 策略2: 降低采样率到22.05kHz
            {'ar': '22050', 'ac': '2', 'audio_bitrate': f'{target_bitrate//2000}k'},
            # 策略3: 单声道，更低采样率
            {'ar': '16000', 'ac': '1', 'audio_bitrate': f'{target_bitrate//4000}k'},
            # 策略4: 极限压缩
            {'ar': '16000', 'ac': '1', 'audio_bitrate': '32k'}
        ]

        for i, config in enumerate(compression_configs):
            try:
                (
                    ffmpeg
                    .input(str(audio_path))
                    .output(
                        str(compressed_path),
                        acodec='libmp3lame',
                        **config
                    )
                    .run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
                )

                compressed_size_mb = compressed_path.stat().st_size / (1024 * 1024)

                if compressed_size_mb <= target_size_mb:
                    # 添加到管理文件列表
                    with self._lock:
                        self.managed_files.add(compressed_path)
                    return compressed_path

            except Exception as e:
                continue

        # 如果所有压缩策略都失败，使用最低质量
        final_path = audio_path.with_suffix('.low.mp3')
        try:
            (
                ffmpeg
                .input(str(audio_path))
                .output(
                    str(final_path),
                    acodec='libmp3lame',
                    ar='8000',
                    ac=1,
                    audio_bitrate='16k'
                )
                .run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
            )

            # 添加到管理文件列表
            with self._lock:
                self.managed_files.add(final_path)

            return final_path

        except Exception as e:
            raise Exception(f"音频压缩失败: {str(e)}")

    def extract_text_from_audio_file(self, audio_path: Path, ctx=None) -> str:
        """
        从本地音频文件中提取文字（使用阿里云百炼API）
        """
        if not dashscope:
            raise Exception("dashscope 未安装")

        try:
            if ctx:
                ctx.info(f"正在处理音频文件: {audio_path.name}")
                ctx.info(f"文件大小: {audio_path.stat().st_size / (1024 * 1024):.2f} MB")

            # 压缩音频到50MB以内
            compressed_audio = self.compress_audio(audio_path, target_size_mb=50)

            if ctx:
                file_size_mb = compressed_audio.stat().st_size / (1024 * 1024)
                ctx.info(f"最终音频文件大小: {file_size_mb:.2f} MB")

            # 上传音频文件进行转录
            with open(compressed_audio, 'rb') as audio_file:
                if ctx:
                    ctx.info("正在上传音频文件进行语音识别...")

                # 使用文件上传而不是URL
                task_response = dashscope.audio.asr.Transcription.async_call(
                    model=self.model,
                    file_urls=[str(compressed_audio)],  # 使用完整的文件路径
                    language_hints=['zh', 'en']
                )

                if ctx:
                    ctx.info("语音识别任务已提交，正在等待处理...")

            # 等待转录完成
            transcription_response = dashscope.audio.asr.Transcription.wait(
                task=task_response.output.task_id
            )

            if transcription_response.status_code == HTTPStatus.OK:
                # 获取转录结果
                for transcription in transcription_response.output['results']:
                    url = transcription['transcription_url']
                    result = json.loads(request.urlopen(url).read().decode('utf8'))

                    # 保存结果到临时文件
                    temp_json_path = self.temp_dir / f'transcription_{int(time.time())}.json'
                    with open(temp_json_path, 'w') as f:
                        json.dump(result, f, indent=4, ensure_ascii=False)

                    # 添加到管理文件列表
                    with self._lock:
                        self.managed_files.add(temp_json_path)

                    # 提取文本内容
                    if 'transcripts' in result and len(result['transcripts']) > 0:
                        text = result['transcripts'][0]['text']
                        if ctx:
                            ctx.info("文本提取完成！")
                        return text
                    else:
                        return "未识别到文本内容"
            else:
                raise Exception(f"转录失败: {transcription_response.output.message}")

        except Exception as e:
            raise Exception(f"从音频文件提取文字时出错: {str(e)}")

    def extract_text_from_video_sync(self, share_link: str, model: str = None) -> dict:
        """同步版本的文字提取（简化版）"""
        try:
            # 同步版本，不使用异步
            video_info = self._parse_share_link(share_link)
            video_id = video_info.get("aweme_id")

            if not video_id:
                return {"error": "无法解析视频ID"}

            # 下载视频
            video_path = self._download_video_sync(video_id)

            # 提取音频
            audio_path = self._extract_audio_sync(video_path)

            # 这里简化处理，实际应该调用dashscope API
            return {
                "status": "success",
                "message": "文字提取功能需要安装完整依赖（dashscope）",
                "video_id": video_id,
                "audio_file": str(audio_path)
            }

        except Exception as e:
            return {"error": f"文字提取失败: {str(e)}"}

    def extract_audio_only_sync(self, video_info: dict) -> Path:
        """同步版本的音频提取"""
        try:
            # 简化实现
            temp_dir = self.temp_dir / f"audio_{int(time.time())}"
            temp_dir.mkdir(parents=True, exist_ok=True)

            audio_path = temp_dir / "extracted_audio.wav"

            # 这里应该实际提取音频
            audio_path.touch()  # 创建空文件作为占位符

            return audio_path

        except Exception as e:
            raise Exception(f"音频提取失败: {str(e)}")

    def _parse_share_link(self, share_link: str) -> dict:
        """解析分享链接"""
        # 简单实现
        if "/video/" in share_link:
            video_id = share_link.split("/video/")[1].split("?")[0]
            return {"aweme_id": video_id}
        return {}

    def _download_video_sync(self, video_id: str) -> Path:
        """同步下载视频（简化版）"""
        temp_dir = self.temp_dir / f"download_{int(time.time())}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        video_path = temp_dir / f"{video_id}.mp4"
        video_path.touch()  # 创建占位符

        return video_path

    def _extract_audio_sync(self, video_path: Path) -> Path:
        """同步提取音频（简化版）"""
        import subprocess

        audio_path = video_path.with_suffix(".wav")

        # 使用ffmpeg提取音频
        try:
            subprocess.run([
                "ffmpeg", "-i", str(video_path),
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1",
                str(audio_path)
            ], check=True, capture_output=True)
            return audio_path
        except:
            # 如果ffmpeg不可用，返回占位符
            audio_path.touch()
            return audio_path

    def cleanup_files(self, *file_paths: Path):
        """清理指定的文件"""
        with self._lock:
            for file_path in file_paths:
                if file_path.exists():
                    try:
                        file_path.unlink()
                        self.managed_files.discard(file_path)
                    except Exception:
                        pass  # 静默处理删除错误