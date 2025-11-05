"""OpenSSH同步工具命令行接口"""

import os
import click
import json
from pathlib import Path
from typing import Optional

from .config import Config, create_default_config
from .main import OpenSSHSync, create_sync


@click.group()
@click.version_option(version="1.0.0", message="OpenSSH同步工具版本 %(version)s")
def main():
    """OpenSSH同步工具
    
    一个用于自动同步OpenSSH最新版本的命令行工具。
    
    示例用法:
        # 查看版本
        openssh-sync --version
        
        # 查看帮助
        openssh-sync --help
        
        # 查看可用命令
        openssh-sync
        
        # 启动守护进程
        openssh-sync daemon
        
        # 执行一次性同步
        openssh-sync sync
        
        # 查看可用版本
        openssh-sync list
    """
    pass


@main.command()
@click.option('--interval', '-i', 
              type=int, 
              default=lambda: int(os.getenv('CHECK_INTERVAL', 24)),
              help='检查间隔时间（小时），示例: 24（默认使用环境变量CHECK_INTERVAL或24）')
@click.option('--dir', '-d', 
              type=click.Path(),
              default=lambda: os.getenv('DOWNLOAD_DIR', './downloads'),
              help='下载目录路径，示例: /tmp/openssh（默认使用环境变量DOWNLOAD_DIR或./downloads）')
@click.option('--min-version', 
              type=str,
              default=lambda: os.getenv('MIN_VERSION', '10.2.1'),
              help='最低版本要求，示例: 10.2.1（默认使用环境变量MIN_VERSION或10.2.1）')
@click.option('--debug', 
              is_flag=True,
              default=lambda: os.getenv('DEBUG', 'false').lower() == 'true',
              help='启用调试模式（默认使用环境变量DEBUG或false）')
def sync(interval: int, dir: str, min_version: str, debug: bool):
    """执行一次性同步操作
    
    所有参数都支持通过环境变量设置默认值，命令行参数会覆盖环境变量。
    
    参数:
        interval: 检查间隔时间（小时），默认从环境变量CHECK_INTERVAL获取
        dir: 下载目录路径，默认从环境变量DOWNLOAD_DIR获取
        min_version: 最低版本要求，默认从环境变量MIN_VERSION获取
        debug: 是否启用调试模式，默认从环境变量DEBUG获取
        
    示例:
        # 使用环境变量配置执行同步（推荐容器环境使用）
        export CHECK_INTERVAL=24
        export DOWNLOAD_DIR=/opt/openssh
        export MIN_VERSION=10.2.1
        export DEBUG=false
        openssh-sync sync
        
        # 使用自定义参数执行同步
        openssh-sync sync --interval 48 --dir /opt/openssh --min-version 10.2.1
        
    环境变量:
        CHECK_INTERVAL: 检查间隔时间（小时），默认24
        DOWNLOAD_DIR: 下载目录路径，默认./downloads
        MIN_VERSION: 最低版本要求（格式: 10.2.1），默认10.2.1
        DEBUG: 是否启用调试模式（true/false），默认false
    """
    try:
        # 创建配置，参数默认值已从环境变量获取
        config = create_default_config()
        
        # 使用命令行参数覆盖默认值
        config.check_interval = interval
        config.download_dir = dir
        
        # 解析版本字符串
        version_parts = min_version.split('.')
        if len(version_parts) == 3:
            config.min_version = (int(version_parts[0]), int(version_parts[1]), int(version_parts[2]))
        
        config.debug = debug
        
        # 验证配置
        if not config.validate():
            return
        
        # 创建同步实例并执行
        sync_tool = create_sync(config)
        
        click.echo("开始执行OpenSSH同步...")
        click.echo(f"检查间隔: {config.check_interval} 小时")
        click.echo(f"下载目录: {config.download_dir}")
        click.echo(f"最小版本: {'.'.join(map(str, config.min_version))}")
        click.echo("-" * 50)
        
        success = sync_tool.sync_files()
        
        if success:
            click.echo("✅ 同步操作完成")
        else:
            click.echo("❌ 同步操作失败")
            
    except Exception as e:
        click.echo(f"❌ 同步过程中发生错误: {e}")


@main.command()
@click.option('--interval', '-i', 
              type=int, 
              default=lambda: int(os.getenv('CHECK_INTERVAL', 24)),
              help='检查间隔时间（小时），示例: 24（默认使用环境变量CHECK_INTERVAL或24）')
@click.option('--dir', '-d', 
              type=click.Path(),
              default=lambda: os.getenv('DOWNLOAD_DIR', './downloads'),
              help='下载目录路径，示例: /tmp/openssh（默认使用环境变量DOWNLOAD_DIR或./downloads）')
def daemon(interval: int, dir: str):
    """启动定时同步守护进程
    
    所有参数都支持通过环境变量设置默认值，命令行参数会覆盖环境变量。
    
    参数:
        interval: 检查间隔时间（小时），默认从环境变量CHECK_INTERVAL获取
        dir: 下载目录路径，默认从环境变量DOWNLOAD_DIR获取
        
    示例:
        # 使用环境变量配置启动守护进程（推荐容器环境使用）
        export CHECK_INTERVAL=24
        export DOWNLOAD_DIR=/opt/openssh
        openssh-sync daemon
        
        # 使用自定义参数启动守护进程
        openssh-sync daemon --interval 48 --dir /opt/openssh
        
    环境变量:
        CHECK_INTERVAL: 检查间隔时间（小时），默认24
        DOWNLOAD_DIR: 下载目录路径，默认./downloads
        MIN_VERSION: 最低版本要求（格式: 10.2.1），默认10.2.1
    """
    try:
        # 创建配置，参数默认值已从环境变量获取
        config = create_default_config()
        
        # 使用命令行参数覆盖默认值
        config.check_interval = interval
        config.download_dir = dir
        
        # 验证配置
        if not config.validate():
            return
        
        # 创建同步实例
        sync_tool = create_sync(config)
        
        click.echo("🚀 启动OpenSSH后台守护进程...")
        click.echo(f"📊 检查间隔: {config.check_interval} 小时")
        click.echo(f"📁 下载目录: {config.download_dir}")
        click.echo("🔄 守护模式: 无限循环")
        click.echo("⏹️  按 Ctrl+C 停止服务")
        click.echo("-" * 50)
        
        # 启动后台守护进程
        sync_tool.start_daemon()
        
    except KeyboardInterrupt:
        click.echo("\n👋 服务已停止")
    except Exception as e:
        click.echo(f"❌ 守护进程启动失败: {e}")





@main.command()
def list():
    """列出可用的OpenSSH版本
    
    示例:
        # 列出可用版本
        openssh-sync list
    """
    try:
        # 创建默认配置
        config = create_default_config()
        sync_tool = create_sync(config)
        
        click.echo("🔍 正在获取OpenSSH版本列表...")
        
        files = sync_tool.get_file_list()
        
        if not files:
            click.echo("❌ 未找到符合条件的OpenSSH版本")
            return
        
        click.echo(f"📋 找到 {len(files)} 个符合条件的版本:")
        click.echo("-" * 60)
        
        for file_info in files:
            version = file_info['version']
            filename = file_info['filename']
            size = file_info.get('size', '未知大小')
            
            click.echo(f"🔸 openssh-{version[0]}.{version[1]}p{version[2]}")
            click.echo(f"   文件: {filename}")
            click.echo(f"   大小: {size}")
            click.echo()
        
        click.echo("💡 提示: 使用 'openssh-sync sync' 命令下载这些版本")
        
    except Exception as e:
        click.echo(f"❌ 获取版本列表失败: {e}")


if __name__ == '__main__':
    main()