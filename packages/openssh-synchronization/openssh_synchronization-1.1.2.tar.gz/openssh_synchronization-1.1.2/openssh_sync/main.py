"""OpenSSH同步主模块"""

import time
from typing import List, Dict

from .config import Config
from .fetcher import create_fetcher
from .downloader import create_downloader
from .html_generator import create_html_generator


class OpenSSHSync:
    """OpenSSH资源同步类"""

    def __init__(self, config: Config):
        """使用配置初始化
        
        参数:
            config: 配置对象
        """
        self.config = config
        self.fetcher = create_fetcher()
        self.downloader = create_downloader(
            download_dir=config.download_dir,
            check_interval=config.check_interval
        )
        self.html_generator = create_html_generator(config.download_dir)
        self.min_version = config.min_version
    
    def get_file_list(self) -> List[Dict[str, str]]:
        """从阿里云镜像获取文件列表
        
        返回:
            文件信息字典列表
        """
        return self.fetcher.fetch_file_list(self.min_version)
    
    def sync_files(self) -> bool:
        """同步OpenSSH文件
        
        返回:
            True表示找到并处理了文件，False表示未找到文件
        """
        print("开始OpenSSH同步...")
        
        # 获取可用文件列表
        files = self.get_file_list()
        if not files:
            print("未找到符合条件的文件")
            print("将在下次检查间隔时重新检查")
            return False  # 返回False表示没有找到文件，但守护进程会继续运行
        
        print(f"找到 {len(files)} 个符合条件的文件")
        
        downloaded_count = self.downloader.download_files(files)
        
        # 生成HTML文件列表
        if downloaded_count > 0:
            print("生成HTML文件列表...")
            self.html_generator.generate_index_html()
        
        print(f"同步完成。下载了 {downloaded_count} 个新文件。")
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
    """创建新的OpenSSH同步实例
    
    参数:
        config: 配置对象
        
    返回:
        OpenSSHSync实例
    """
    return OpenSSHSync(config)