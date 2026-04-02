# -*- coding: utf-8 -*-
import os
import tarfile
import py7zr

def extract_archive(archive_path, extract_to='.'):
    """根据后缀名，自动解压 .tar.gz 或 .7z 文件"""
    # 确保目标目录存在
    os.makedirs(extract_to, exist_ok=True)

    if archive_path.endswith('.tar.gz'):
        try:
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(path=extract_to)
            print(f"✅ 已解压 {archive_path} 到 {extract_to}")
            return True
        except Exception as e:
            print(f"❌ 解压失败 {archive_path}: {e}")
            return False
    elif archive_path.endswith('.7z'):
        try:
            with py7zr.SevenZipFile(archive_path, mode='r') as archive:
                archive.extractall(path=extract_to)
            print(f"✅ 已解压 {archive_path} 到 {extract_to}")
            return True
        except Exception as e:
            print(f"❌ 解压失败 {archive_path}: {e}")
            return False
    else:
        print(f"❌ 不支持的文件格式: {archive_path}")
        return False

# 使用示例
if __name__ == "__main__":
    extract_archive("downloaded_file.tar.gz", "extracted_contents")
    extract_archive("downloaded_file.7z", "extracted_contents")
