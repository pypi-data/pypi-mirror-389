"""OpenSSH同步工具命令行接口"""

import os
import click

from .config import create_default_config
from .main import create_sync
from . import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """OpenSSH同步工具"""
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
@click.option('--auto-register', is_flag=True, help='自动检测并注册systemd服务')
def daemon(interval: int, dir: str, auto_register: bool):
    """启动定时同步守护进程
    
    所有参数都支持通过环境变量设置默认值，命令行参数会覆盖环境变量。
    如果使用 --auto-register 参数，会自动检测并注册systemd服务。
    
    参数:
        interval: 检查间隔时间（小时），默认从环境变量CHECK_INTERVAL获取
        dir: 下载目录路径，默认从环境变量DOWNLOAD_DIR获取
        auto_register: 是否自动注册systemd服务
        
    示例:
        # 使用环境变量配置启动守护进程（推荐容器环境使用）
        export CHECK_INTERVAL=24
        export DOWNLOAD_DIR=/opt/openssh
        openssh-sync daemon
        
        # 使用自定义参数启动守护进程
        openssh-sync daemon --interval 48 --dir /opt/openssh
        
        # 自动注册systemd服务并启动守护进程
        openssh-sync daemon --auto-register
        
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
        
        # 自动注册systemd服务
        if auto_register:
            try:
                from plsm import ServiceManager, ServiceConfig
                
                manager = ServiceManager(sudo=True)
                service_name = 'openssh-sync'
                
                # 检查服务是否已存在
                service_info = manager.get_service_info(service_name)
                
                if not service_info:
                    click.echo("🔍 检测到服务未注册，正在自动注册...")
                    
                    # 获取当前脚本路径
                    import sys
                    executable = sys.executable
                    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cli.py')
                    
                    # 创建服务配置
                    service_config = ServiceConfig(
                        name=service_name,
                        description='OpenSSH Synchronization Service',
                        exec_start=f'{executable} {script_path} daemon --interval {interval} --dir {dir}',
                        working_directory=os.getcwd(),
                        user='root',
                        group='root',
                        restart='always',
                        environment={
                            'DOWNLOAD_DIR': dir,
                            'CHECK_INTERVAL': str(interval),
                            'MIN_VERSION': '10.2.1'
                        }
                    )
                    
                    # 创建服务
                    result = manager.create_service(service_config)
                    
                    if result:
                        click.echo("✅ 服务注册成功")
                        manager.enable_service(service_name)
                        click.echo("✅ 服务已启用")
                        manager.start_service(service_name)
                        click.echo("✅ 服务已启动")
                        click.echo("💡 服务已注册为systemd服务，将自动运行")
                        return
                    else:
                        click.echo("⚠️  服务注册失败，继续以普通模式运行")
                else:
                    click.echo(f"✅ 服务 '{service_name}' 已存在，状态: {service_info.status.value}")
                    
            except ImportError:
                click.echo("⚠️  plsm库未安装，无法自动注册服务")
            except Exception as e:
                click.echo(f"⚠️  自动注册服务失败: {e}，继续以普通模式运行")
        
        # 创建同步实例
        sync_tool = create_sync(config)
        
        click.echo("🚀 启动OpenSSH后台守护进程...")
        click.echo(f"📊 检查间隔: {config.check_interval} 小时")
        click.echo(f"📁 下载目录: {config.download_dir}")
        if auto_register:
            click.echo("🔧 服务模式: systemd服务")
        else:
            click.echo("🔧 服务模式: 普通进程")
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


@main.command()
@click.option('--force', '-f', is_flag=True, help='强制重新注册服务')
def register(force: bool):
    """注册OpenSSH同步服务到systemd
    
    此命令会自动检测服务是否已注册，如果未注册则自动注册。
    如果服务已存在，可以使用 --force 参数强制重新注册。
    
    示例:
        # 自动检测并注册服务
        openssh-sync register
        
        # 强制重新注册服务
        openssh-sync register --force
    """
    try:
        from plsm import ServiceManager, ServiceConfig
        
        # 创建服务管理器
        manager = ServiceManager(sudo=True)
        service_name = 'openssh-sync'
        
        # 检查服务是否已存在
        service_info = manager.get_service_info(service_name)
        
        if service_info and not force:
            click.echo(f"✅ 服务 '{service_name}' 已存在")
            click.echo(f"   状态: {service_info.status.value}")
            click.echo("💡 如需重新注册，请使用 'openssh-sync register --force'")
            return
        
        if service_info and force:
            click.echo(f"🔄 强制重新注册服务 '{service_name}'...")
            # 先移除现有服务
            manager.remove_service(service_name)
            click.echo("✅ 已移除现有服务")
        
        # 获取当前脚本路径
        import sys
        executable = sys.executable
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cli.py')
        
        # 创建服务配置
        config = ServiceConfig(
            name=service_name,
            description='OpenSSH Synchronization Service',
            exec_start=f'{executable} {script_path} daemon',
            working_directory=os.getcwd(),
            user='root',
            group='root',
            restart='always',
            environment={
                'DOWNLOAD_DIR': '/opt/openssh',
                'CHECK_INTERVAL': '24',
                'MIN_VERSION': '10.2.1'
            }
        )
        
        click.echo(f"🚀 正在注册服务 '{service_name}'...")
        click.echo(f"   服务名称: {config.name}")
        click.echo(f"   服务描述: {config.description}")
        click.echo(f"   启动命令: {config.exec_start}")
        click.echo(f"   工作目录: {config.working_directory}")
        
        # 创建服务
        result = manager.create_service(config)
        
        if result:
            click.echo("✅ 服务注册成功")
            
            # 启用服务
            manager.enable_service(service_name)
            click.echo("✅ 服务已启用")
            
            # 启动服务
            manager.start_service(service_name)
            click.echo("✅ 服务已启动")
            
            click.echo("\n📋 服务信息:")
            service_info = manager.get_service_info(service_name)
            click.echo(f"   状态: {service_info.status.value}")
            click.echo(f"   是否加载: {service_info.loaded}")
            click.echo(f"   是否运行: {service_info.running}")
            
            click.echo("\n💡 服务管理命令:")
            click.echo("   sudo systemctl status openssh-sync    # 查看服务状态")
            click.echo("   sudo systemctl start openssh-sync     # 启动服务")
            click.echo("   sudo systemctl stop openssh-sync      # 停止服务")
            click.echo("   sudo systemctl restart openssh-sync  # 重启服务")
            
        else:
            click.echo("❌ 服务注册失败")
            
    except ImportError:
        click.echo("❌ 未找到plsm库，请先安装: pip install plsm")
    except Exception as e:
        click.echo(f"❌ 服务注册过程中发生错误: {e}")


@main.command()
def status():
    """查看OpenSSH同步服务状态
    
    示例:
        # 查看服务状态
        openssh-sync status
    """
    try:
        from plsm import ServiceManager
        
        # 创建服务管理器
        manager = ServiceManager(sudo=True)
        service_name = 'openssh-sync'
        
        # 获取服务信息
        service_info = manager.get_service_info(service_name)
        
        if not service_info:
            click.echo(f"❌ 服务 '{service_name}' 不存在")
            click.echo("💡 请使用 'openssh-sync register' 注册服务")
            return
        
        click.echo(f"📊 服务 '{service_name}' 状态:")
        click.echo(f"   状态: {service_info.status.value}")
        click.echo(f"   是否加载: {service_info.loaded}")
        click.echo(f"   是否运行: {service_info.running}")
        
        # 检查服务健康状态
        is_healthy = manager.is_service_healthy(service_name)
        click.echo(f"   健康状态: {'✅ 健康' if is_healthy else '❌ 异常'}")
        
        # 获取服务日志（最近10行）
        try:
            logs = manager.get_service_logs(service_name, lines=10)
            if logs:
                click.echo("\n📋 最近日志:")
                # 日志返回的是字符串，按行分割
                log_lines = logs.strip().split('\n')
                for log in log_lines[-10:]:  # 只显示最后10行
                    click.echo(f"   {log}")
        except Exception as e:
            click.echo(f"   日志获取失败: {e}")
            
    except ImportError:
        click.echo("❌ 未找到plsm库，请先安装: pip install plsm")
    except Exception as e:
        click.echo(f"❌ 获取服务状态失败: {e}")


@main.command()
@click.option('--force', '-f', is_flag=True, help='强制删除服务')
def unregister(force: bool):
    """从systemd中删除OpenSSH同步服务
    
    示例:
        # 删除服务
        openssh-sync unregister
        
        # 强制删除服务（即使服务正在运行）
        openssh-sync unregister --force
    """
    try:
        from plsm import ServiceManager
        
        # 创建服务管理器
        manager = ServiceManager(sudo=True)
        service_name = 'openssh-sync'
        
        # 检查服务是否存在
        service_info = manager.get_service_info(service_name)
        
        if not service_info:
            click.echo(f"❌ 服务 '{service_name}' 不存在")
            return
        
        click.echo(f"🗑️  正在删除服务 '{service_name}'...")
        
        # 如果服务正在运行，先停止
        if service_info.status.value == 'active':
            if force:
                manager.stop_service(service_name)
                click.echo("✅ 服务已停止")
            else:
                click.echo("⚠️  服务正在运行，请先停止服务或使用 --force 参数")
                return
        
        # 删除服务
        result = manager.remove_service(service_name)
        
        if result:
            click.echo("✅ 服务删除成功")
        else:
            click.echo("❌ 服务删除失败")
            
    except ImportError:
        click.echo("❌ 未找到plsm库，请先安装: pip install plsm")
    except Exception as e:
        click.echo(f"❌ 服务删除过程中发生错误: {e}")


if __name__ == '__main__':
    main()