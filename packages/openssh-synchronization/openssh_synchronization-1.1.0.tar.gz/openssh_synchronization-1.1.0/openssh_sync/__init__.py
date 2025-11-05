"""OpenSSH资源同步工具"""

__version__ = "1.1.0"
__author__ = "坐公交也用券"
__email__ = "liumou.site@qq.com"

from openssh_sync.main import OpenSSHSync
from openssh_sync.config import Config
from openssh_sync.fetcher import OpenSSHFetcher, create_fetcher
from openssh_sync.downloader import OpenSSHDownloader, create_downloader
from openssh_sync.utils import (
    parse_version,
    is_version_greater_or_equal,
    download_file,
)

__all__ = [
    "OpenSSHSync",
    "Config",
    "OpenSSHFetcher",
    "create_fetcher",
    "OpenSSHDownloader",
    "create_downloader",
    "parse_version",
    "is_version_greater_or_equal",
    "download_file",
]