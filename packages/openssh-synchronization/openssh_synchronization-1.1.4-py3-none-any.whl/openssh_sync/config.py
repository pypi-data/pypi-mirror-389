"""OpenSSH同步工具配置模块"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """OpenSSH同步配置类
    
    示例:
        config = Config(
            check_interval=24,  # 每24小时检查一次
            download_dir="/tmp/openssh"  # 下载目录
        )
    """
    
    # 检查间隔时间（小时），最小值为12小时
    # 示例值: 24 (表示每24小时检查一次)
    check_interval: int = 24
    
    # 下载文件保存目录
    # 示例值: "/tmp/openssh" 或 "./downloads"
    download_dir: str = "./downloads"
    
    # 最小版本要求，格式为 (主版本, 次版本, 修订版本)
    # 示例值: (10, 2, 1) 对应 openssh-10.2p1
    min_version: tuple = (10, 2, 1)
    
    # 镜像源URL
    # 示例值: "https://mirrors.aliyun.com/openssh/portable"
    mirror_url: str = "https://mirrors.aliyun.com/openssh/portable"
    
    # 请求超时时间（秒）
    # 示例值: 30 (30秒超时)
    timeout: int = 30
    
    # 是否启用调试模式
    # 示例值: True (显示详细日志) 或 False (仅显示基本信息)
    debug: bool = False
    
    def validate(self) -> bool:
        """验证配置参数的有效性
        
        返回:
            bool: 配置是否有效
            
        示例:
            config = Config(check_interval=6)  # 无效，小于12小时
            if not config.validate():
                print("配置验证失败")
        """
        # 注意：check_interval会在__post_init__中自动调整，这里不需要重复验证
        
        if not self.download_dir:
            print("错误: 下载目录不能为空")
            return False
            
        if not isinstance(self.min_version, (tuple, list)) or len(self.min_version) != 3:
            print("错误: 版本格式不正确，应为(主版本, 次版本, 修订版本)")
            return False
            
        if self.timeout <= 0:
            print("错误: 超时时间必须大于0")
            return False
            
        return True
    
    def __post_init__(self):
        """初始化后处理，确保配置合理性
        
        示例:
            config = Config(check_interval=6)  # 自动调整为12小时
            print(config.check_interval)  # 输出: 12
        """
        # 确保检查间隔不小于12小时
        if self.check_interval < 12:
            print(f"警告: 检查间隔时间{self.check_interval}小时小于最小值12小时，已自动调整为12小时")
            self.check_interval = 12
            
        # 确保下载目录不以斜杠结尾
        if self.download_dir.endswith('/'):
            self.download_dir = self.download_dir[:-1]


def create_default_config() -> Config:
    """创建默认配置，支持环境变量
    
    返回:
        Config: 默认配置实例，优先使用环境变量
        
    示例:
        config = create_default_config()
        print(config.check_interval)  # 输出: 24 或环境变量值
    """
    # 从环境变量读取配置，如果未设置则使用默认值
    check_interval = int(os.getenv('CHECK_INTERVAL', 24))
    download_dir = os.getenv('DOWNLOAD_DIR', './downloads')
    min_version_str = os.getenv('MIN_VERSION', '10.2.1')
    
    # 解析版本字符串
    min_version_parts = min_version_str.split('.')
    if len(min_version_parts) == 3:
        min_version = (int(min_version_parts[0]), int(min_version_parts[1]), int(min_version_parts[2]))
    else:
        min_version = (10, 2, 1)
    
    return Config(
        check_interval=check_interval,
        download_dir=download_dir,
        min_version=min_version
    )