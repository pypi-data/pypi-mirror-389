"""OpenSSH synchronization main module."""

import re
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from pathlib import Path

from .config import Config
from .utils import (
    parse_version,
    is_version_greater_or_equal,
    download_file,
    get_file_modification_time,
)


class OpenSSHSync:
    """OpenSSH resource synchronization class."""

    def __init__(self, config: Config):
        """Initialize with configuration.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.base_url = "https://mirrors.aliyun.com/openssh/portable"
        self.min_version = config.min_version  # 使用配置中的最小版本
        
    def get_file_list(self) -> List[Dict[str, str]]:
        """Get list of files from Aliyun mirror.
        
        Returns:
            List of file information dictionaries
        """
        try:
            response = requests.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            files = []
            
            # Find all file links
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.endswith('.tar.gz') and 'openssh-' in href:
                    # Extract version from filename
                    version_match = re.search(r'openssh-(\d+)\.(\d+)p(\d+)', href)
                    if version_match:
                        major = int(version_match.group(1))
                        minor = int(version_match.group(2))
                        patch = int(version_match.group(3))
                        
                        # Check if version meets minimum requirement
                        if is_version_greater_or_equal((major, minor, patch), self.min_version):
                            files.append({
                                'filename': href,
                                'url': f"{self.base_url}/{href}",
                                'version': (major, minor, patch),
                                'size': link.find_next_sibling(string=re.compile(r'\d+\.\d+ [KMG]B'))
                            })
            
            return sorted(files, key=lambda x: x['version'], reverse=True)
            
        except requests.RequestException as e:
            print(f"Error fetching file list: {e}")
            return []
    
    def should_download(self, filename: str, local_path: Path) -> bool:
        """Check if file should be downloaded.
        
        Args:
            filename: Name of the file
            local_path: Local path to check
            
        Returns:
            True if file should be downloaded
        """
        file_path = local_path / filename
        
        # If file doesn't exist, download it
        if not file_path.exists():
            return True
        
        # Check if file is older than the minimum interval
        if self.config.check_interval > 0:
            file_mtime = get_file_modification_time(file_path)
            current_time = time.time()
            
            # Convert hours to seconds
            interval_seconds = self.config.check_interval * 3600
            
            if current_time - file_mtime > interval_seconds:
                return True
        
        return False
    
    def sync_files(self) -> bool:
        """Synchronize OpenSSH files.
        
        Returns:
            True if files were found and processed, False if no files found
        """
        print("Starting OpenSSH synchronization...")
        
        # Create download directory if it doesn't exist
        download_dir = Path(self.config.download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # Get list of available files
        files = self.get_file_list()
        if not files:
            print("No files found matching criteria")
            print("Will check again at next interval")
            return False  # 返回False表示没有找到文件，但守护进程会继续运行
        
        print(f"Found {len(files)} files meeting criteria")
        
        downloaded_count = 0
        for file_info in files:
            filename = file_info['filename']
            url = file_info['url']
            
            if self.should_download(filename, download_dir):
                print(f"Downloading: {filename}")
                
                if download_file(url, download_dir / filename):
                    downloaded_count += 1
                    print(f"Successfully downloaded: {filename}")
                else:
                    print(f"Failed to download: {filename}")
            else:
                print(f"Skipping (up to date): {filename}")
        
        print(f"Synchronization completed. Downloaded {downloaded_count} new files.")
        return True
    
    def start_daemon(self):
        """启动后台守护进程，使用无限循环实现定时同步。"""
        if self.config.check_interval < 12:
            print("警告: 检查间隔小于12小时。最小间隔为12小时。")
            self.config.check_interval = 12
        
        print(f"启动后台守护进程，检查间隔: {self.config.check_interval} 小时")
        print("守护进程已启动，按 Ctrl+C 停止")
        
        # 立即执行一次同步
        self.sync_files()
        
        # 无限循环实现定时同步
        try:
            while True:
                # 计算下次同步的时间
                interval_seconds = self.config.check_interval * 3600
                print(f"下次同步将在 {self.config.check_interval} 小时后进行...")
                
                # 等待指定间隔
                time.sleep(interval_seconds)
                
                # 执行同步
                self.sync_files()
                
        except KeyboardInterrupt:
            print("\n守护进程已停止")
        except Exception as e:
            print(f"守护进程异常: {e}")
            print("守护进程将在5秒后重启...")
            time.sleep(5)
            self.start_daemon()  # 重启守护进程


def create_sync(config: Config) -> OpenSSHSync:
    """Create a new OpenSSH synchronization instance.
    
    Args:
        config: Configuration object
        
    Returns:
        OpenSSHSync instance
    """
    return OpenSSHSync(config)