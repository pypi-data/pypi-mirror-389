"""OpenSSH resource synchronization tool."""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from openssh_sync.main import OpenSSHSync
from openssh_sync.config import Config
from openssh_sync.utils import (
    parse_version,
    is_version_greater_or_equal,
    download_file,
)

__all__ = [
    "OpenSSHSync",
    "Config",
    "parse_version",
    "is_version_greater_or_equal",
    "download_file",
]