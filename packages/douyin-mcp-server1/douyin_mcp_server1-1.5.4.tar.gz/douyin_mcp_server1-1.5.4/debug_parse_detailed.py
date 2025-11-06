#!/usr/bin/env python3
"""详细调试抖音解析过程"""

import sys
import os
import requests
import re
import json

# 使用原版的headers
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 Version/17.0 Mobile/15E148 Safari/604.1'
}

def debug_parse_share_url(share_text: str):
    print("=== 开始解析 ===")
    print(f"输入文本: {share_text[:100]}...\n")

    # 1. 提取分享链接
    try:
        # 尝试多种模式匹配完整的URL
        patterns = [
            r'https?://v\.douyin\.com/[A-Za-z0-9]+',  # 最常见的模式
            r'https?://www\.iesdouyin\.com/share/video/\d+',  # 完整分享页面
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$\-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # 通用模式
        ]

        share_url = None
        for pattern in patterns:
            matches = re.findall(pattern, share_text)
            if matches:
                share_url = matches[0]
                break

        if not share_url:
            print("❌ 未找到有效的分享链接")
            return
        print(f"✓ 提取的分享链接: {share_url}")
    except Exception as e:
        print(f"❌ 提取链接失败: {e}")
        return

    # 2. 访问分享链接获取重定向
    try:
        print("\n--- 访问分享链接 ---")
        share_response = requests.get(share_url, headers=headers, allow_redirects=True)
        print(f"✓ 状态码: {share_response.status_code}")
        print(f"✓ 最终URL: {share_response.url}")

        video_id = share_response.url.split("?")[0].strip("/").split("/")[-1]
        print(f"✓ 视频ID: {video_id}")
    except Exception as e:
        print(f"❌ 访问分享链接失败: {e}")
        return

    # 3. 构造抖音分享页面URL
    share_page_url = f'https://www.iesdouyin.com/share/video/{video_id}'
    print(f"\n--- 构造页面URL ---")
    print(f"✓ 页面URL: {share_page_url}")

    # 4. 获取页面内容
    try:
        print("\n--- 获取页面内容 ---")
        response = requests.get(share_page_url, headers=headers)
        print(f"✓ 状态码: {response.status_code}")
        print(f"✓ 内容长度: {len(response.text)} 字节")

        # 查找 window._ROUTER_DATA
        pattern = re.compile(
            pattern=r"window\._ROUTER_DATA\s*=\s*(.*?)</script>",
            flags=re.DOTALL,
        )

        find_res = pattern.search(response.text)
        if not find_res:
            print("❌ 未找到 window._ROUTER_DATA")
            print("\n页面内容片段:")
            print(response.text[:500] + "...")
            return

        print(f"✓ 找到 window._ROUTER_DATA")

        # 5. 解析JSON
        try:
            print("\n--- 解析JSON数据 ---")
            json_str = find_res.group(1).strip()
            print(f"JSON字符串长度: {len(json_str)} 字符")

            # 尝试解析JSON
            json_data = json.loads(json_str)
            print(f"✓ JSON解析成功")
            print(f"  - 键: {list(json_data.keys())}")

            # 检查 loaderData
            if "loaderData" not in json_data:
                print("❌ JSON中没有 loaderData 键")
                return

            loader_data = json_data["loaderData"]
            print(f"✓ loaderData 键存在")
            print(f"  - loaderData 键: {list(loader_data.keys())}")

            # 查找视频信息
            VIDEO_ID_PAGE_KEY = "video_(id)/page"
            NOTE_ID_PAGE_KEY = "note_(id)/page"

            original_video_info = None
            if VIDEO_ID_PAGE_KEY in loader_data:
                original_video_info = loader_data[VIDEO_ID_PAGE_KEY]["videoInfoRes"]
                print(f"✓ 找到视频信息 (VIDEO_ID_PAGE_KEY)")
            elif NOTE_ID_PAGE_KEY in loader_data:
                original_video_info = loader_data[NOTE_ID_PAGE_KEY]["videoInfoRes"]
                print(f"✓ 找到视频信息 (NOTE_ID_PAGE_KEY)")
            else:
                print("❌ 未找到视频信息")
                return

            print(f"videoInfoRes 键: {list(original_video_info.keys())}")

            # 6. 获取 item_list
            if "item_list" not in original_video_info:
                print("❌ videoInfoRes 中没有 item_list")
                return

            item_list = original_video_info["item_list"]
            print(f"✓ item_list 长度: {len(item_list)}")

            if not item_list:
                print("❌ item_list 为空")
                return

            # 7. 获取第一个项目
            data = item_list[0]
            print(f"✓ 获取第一个项目")
            print(f"  - 数据键: {list(data.keys())}")

            if "video" not in data:
                print("❌ 项目中没有 video 键")
                return

            video_info = data["video"]
            print(f"✓ video 键存在")

            if "play_addr" not in video_info:
                print("❌ video 中没有 play_addr")
                return

            play_addr = video_info["play_addr"]
            print(f"✓ play_addr 键存在")

            if "url_list" not in play_addr:
                print("❌ play_addr 中没有 url_list")
                return

            url_list = play_addr["url_list"]
            print(f"✓ url_list 长度: {len(url_list)}")

            if not url_list:
                print("❌ url_list 为空")
                return

            video_url = url_list[0].replace("playwm", "play")
            print(f"✓ 原始URL: {url_list[0][:100]}...")
            print(f"✓ 处理后URL: {video_url[:100]}...")

            desc = data.get("desc", "").strip() or f"douyin_{video_id}"
            desc = re.sub(r'[\\/:*?"<>|]', '_', desc)
            print(f"✓ 标题: {desc}")

            return {
                "url": video_url,
                "title": desc,
                "video_id": video_id
            }

        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"\n原始JSON片段: {json_str[:200]}...")
            return

    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return

# 测试
share_text = "1.74 o@D.hO nQk:/ 04/24 只讲干货，十五五规划到底说了啥？ # 我在十四五这五年 # 零距离看懂财经  https://v.douyin.com/cGF6wYr0cok/ 复制此链接，打开Dou音搜索，直接观看视频！"

result = debug_parse_share_url(share_text)

if result:
    print("\n=== 解析成功 ===")
    print(f"视频ID: {result['video_id']}")
    print(f"标题: {result['title']}")
    print(f"URL: {result['url'][:100]}...")
else:
    print("\n=== 解析失败 ===")