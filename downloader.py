# -*- coding: utf-8 -*-
"""
断点续传下载工具库
提供远程/本地文件大小获取、断点续传下载、智能检查更新等功能。
"""

__all__ = [
    'check_and_download'
]

import os
import time
import requests
from tqdm import tqdm
from typing import Optional

# 请求头
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

def get_remote_file_size(url:str, timeout:int=10)->int:
    """
    获取远程文件大小（字节），使用 DEFAULT_HEADERS。
    获取失败抛出 ValueError。
    """
    headers = DEFAULT_HEADERS.copy()
    # 方法1: HEAD
    try:
        resp = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        size = resp.headers.get('content-length')
        if size is not None:
            return int(size)
    except:
        pass
    # 方法2: GET stream（只读头）
    try:
        resp = requests.get(url, headers=headers, stream=True, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        size = resp.headers.get('content-length')
        resp.close()
        if size is not None:
            return int(size)
    except:
        pass
    # 方法3: Range 请求（bytes=0-0）
    try:
        range_headers = headers.copy()
        range_headers['Range'] = 'bytes=0-0'
        resp = requests.get(url, headers=range_headers, timeout=timeout, allow_redirects=True)
        if resp.status_code == 206:
            content_range = resp.headers.get('content-range')
            if content_range:
                total = content_range.split('/')[-1]
                if total.isdigit():
                    return int(total)
        resp.close()
    except:
        pass
    raise ValueError("Unable to determine remote file size.")

def get_local_file_size(file_path:str)->Optional[int]:
    try:
        return os.path.getsize(file_path)
    except OSError:
        return None

def download_resumable(
    url: str,
    local_path: str,
    max_retries: int = 999,
    retry_delay: float = 3.0,
    remote_size: Optional[int] = None
) -> bool:
    """断点续传下载文件，带进度条。"""
    headers = DEFAULT_HEADERS.copy()
    total_size = remote_size
    if total_size is None:
        try:
            total_size = get_remote_file_size(url, timeout=10)
        except ValueError:
            total_size = 0

    downloaded = 0
    if os.path.exists(local_path):
        downloaded = os.path.getsize(local_path)

    if total_size > 0 and downloaded == total_size:
        print(f"文件已完整: {local_path}")
        return True

    req_headers = headers.copy()
    if downloaded > 0:
        req_headers['Range'] = f'bytes={downloaded}-'

    retry_count = 0
    pbar = None
    chunk_size = 8192

    while retry_count <= max_retries:
        try:
            resp = requests.get(url, headers=req_headers, stream=True, timeout=30, allow_redirects=True)
            resp.raise_for_status()

            if downloaded > 0 and resp.status_code == 200:
                print("服务器不支持断点续传，从头下载")
                downloaded = 0
                mode = 'wb'
                req_headers.pop('Range', None)
                resp = requests.get(url, headers=req_headers, stream=True, timeout=30, allow_redirects=True)
                resp.raise_for_status()
            else:
                mode = 'ab' if downloaded > 0 else 'wb'

            effective_total = total_size
            if effective_total == 0 and 'content-range' in resp.headers:
                effective_total = int(resp.headers['content-range'].split('/')[-1])
            elif effective_total == 0 and 'content-length' in resp.headers:
                effective_total = int(resp.headers['content-length'])
                if downloaded > 0 and resp.status_code == 206:
                    effective_total += downloaded

            pbar = tqdm(
                total=effective_total if effective_total > 0 else None,
                initial=downloaded,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                desc=os.path.basename(local_path),
                dynamic_ncols=True
            )

            with open(local_path, mode) as f:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        pbar.update(len(chunk))

            pbar.close()
            if effective_total > 0 and downloaded != effective_total:
                raise RuntimeError(f"下载大小不匹配: {downloaded} != {effective_total}")

            print("\n下载完成")
            return True

        except (requests.RequestException, ConnectionError, TimeoutError, RuntimeError) as e:
            if pbar:
                pbar.close()
            retry_count += 1
            if retry_count > max_retries:
                print(f"\n下载失败，已达最大重试次数: {e}")
                return False
            print(f"\n网络错误: {e}，{retry_delay}秒后重试 (第{retry_count}次/{max_retries})")
            time.sleep(retry_delay)
            if os.path.exists(local_path):
                downloaded = os.path.getsize(local_path)
                req_headers = headers.copy()
                req_headers['Range'] = f'bytes={downloaded}-'
            else:
                downloaded = 0
                req_headers = headers.copy()

    return False

def check_and_download(
    url: str,
    local_path: str,
    max_retries: int = 999,
    retry_delay: float = 3.0
) -> bool:
    """先检查远程与本地文件大小，若本地不存在或大小不一致则下载。"""
    try:
        remote_size = get_remote_file_size(url, timeout=10)
    except ValueError as e:
        print(f"警告: 无法获取远程文件大小 ({e})，将尝试下载")
        remote_size = None

    local_size = get_local_file_size(local_path)

    if local_size is not None and remote_size is not None and local_size == remote_size:
        print(f"本地文件已是最新，无需下载: {local_path}")
        return True

    print("开始下载（本地文件缺失或与远程不一致）...")
    return download_resumable(
        url=url,
        local_path=local_path,
        max_retries=max_retries,
        retry_delay=retry_delay,
        remote_size=remote_size
    )
