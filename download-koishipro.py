# -*- coding: utf-8 -*-
import platform
import sys
from typing import Optional
import downloader

def get_download_info() -> Optional[tuple[str, str]]:
    """根据当前平台返回 (下载URL, 本地文件名)"""
    system = platform.system().lower()
    if system == 'windows':
        url = "https://cdntx.moecube.com/koishipro/archive/KoishiPro-master-win32-zh-CN.7z"
        filename = "koishipro.7z"
        return url, filename
    elif system == 'linux':
        url = "https://cdn02.moecube.com:444/koishipro/archive/KoishiPro-master-linux-zh-CN.tar.gz"
        filename = "koishipro.tar.gz"
        return url, filename
    else:
        print(f"不支持的操作系统: {system}")
        return None

if __name__ == "__main__":
    info = get_download_info()
    if info is None:
        sys.exit(1)

    url, local_filename = info
    success = downloader.check_and_download(url, local_filename)
    if success:
        print(f"操作成功，文件保存为: {local_filename}")
    else:
        print("操作失败")
        sys.exit(1)
