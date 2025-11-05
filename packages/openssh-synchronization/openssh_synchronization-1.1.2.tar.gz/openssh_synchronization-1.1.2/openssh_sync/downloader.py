"""OpenSSH下载管理模块"""

import time
from pathlib import Path
from typing import List, Dict

from .utils import download_file, get_file_modification_time


class OpenSSHDownloader:
    """OpenSSH下载管理类"""

    def __init__(self, download_dir: str = "./downloads", check_interval: int = 24):
        """使用下载配置初始化
        
        参数:
            download_dir: 下载文件的目录
            check_interval: 检查间隔（小时）
        """
        self.download_dir = Path(download_dir)
        self.check_interval = check_interval

    def should_download(self, filename: str) -> bool:
        """检查文件是否应该下载
        
        参数:
            filename: 文件名
            
        返回:
            True表示文件应该下载
        """
        file_path = self.download_dir / filename
        
        # 如果文件不存在，下载它
        if not file_path.exists():
            return True
        
        # 检查文件是否比最小间隔更旧
        if self.check_interval > 0:
            file_mtime = get_file_modification_time(file_path)
            current_time = time.time()
            
            # 将小时转换为秒
            interval_seconds = self.check_interval * 3600
            
            if current_time - file_mtime > interval_seconds:
                return True
        
        return False

    def download_files(self, file_list: List[Dict[str, str]]) -> int:
        """从提供的列表中下载文件
        
        参数:
            file_list: 文件信息字典列表
            
        返回:
            成功下载的文件数量
        """
        # 如果下载目录不存在，创建它
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_count = 0
        
        for file_info in file_list:
            filename = file_info['filename']
            url = file_info['url']
            
            if self.should_download(filename):
                print(f"正在下载: {filename}")
                
                if download_file(url, self.download_dir / filename):
                    downloaded_count += 1
                    print(f"成功下载: {filename}")
                else:
                    print(f"下载失败: {filename}")
            else:
                print(f"跳过（已是最新）: {filename}")
        
        return downloaded_count

    def get_local_files(self) -> List[Dict[str, str]]:
        """获取本地下载的文件列表
        
        返回:
            本地文件信息列表
        """
        if not self.download_dir.exists():
            return []
        
        files = []
        for file_path in self.download_dir.glob("*.tar.gz"):
            if file_path.is_file():
                files.append({
                    'filename': file_path.name,
                    'local_path': str(file_path),
                    'size': file_path.stat().st_size if file_path.exists() else 0
                })
        
        return files


def create_downloader(download_dir: str = "./downloads", check_interval: int = 24) -> OpenSSHDownloader:
    """创建新的OpenSSH下载器实例
    
    参数:
        download_dir: 下载文件的目录
        check_interval: 检查间隔（小时）
        
    返回:
        OpenSSHDownloader实例
    """
    return OpenSSHDownloader(download_dir, check_interval)