"""
命令行界面模块
使用 Click 框架实现 CLI 功能
"""

import os
import sys
import click
from typing import List, Optional
import logging

from .core import RepositoryManager
from .decompiler import JavaDecompiler
from .utils import setup_logging, format_size, validate_dependency_format, ProgressTracker
from .config import config_manager

logger = logging.getLogger(__name__)

class ClickProgressTracker:
    """Click 进度条包装器"""
    
    def __init__(self, description: str = "Progress"):
        self.description = description
        self.progress_bar = None
    
    def __call__(self, current: int, total: int, message: str = ""):
        if self.progress_bar is None and total > 0:
            self.progress_bar = click.progressbar(
                length=total,
                label=self.description,
                show_percent=True,
                show_pos=True
            )
        
        if self.progress_bar:
            self.progress_bar.update(current - self.progress_bar.pos)
            
            if current >= total:
                self.progress_bar.finish()

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='启用详细输出')
@click.option('--log-file', help='日志文件路径')
@click.pass_context
def cli(ctx, verbose, log_file):
    """Gradle File Downloader - 从 Gradle 仓库下载依赖源码"""
    # 确保上下文对象存在
    ctx.ensure_object(dict)
    
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level, log_file)
    
    # 存储配置到上下文
    ctx.obj['verbose'] = verbose
    ctx.obj['log_file'] = log_file

@cli.command()
@click.argument('dependency')
@click.option('--output-dir', '-o', default='downloads', help='输出目录')
@click.option('--repositories', '-r', multiple=True, help='自定义仓库 URL')
@click.option('--repo-names', multiple=True, help='指定使用的仓库名称')
@click.option('--decompile', '-d', is_flag=True, help='如果没有源码则强制反编译')
@click.option('--sources-only', '-s', is_flag=True, help='只下载源码，不反编译')
@click.option('--force-binary', '-b', is_flag=True, help='强制下载二进制包并反编译（跳过源码）')
@click.pass_context
def download(ctx, dependency, output_dir, repositories, repo_names, decompile, sources_only, force_binary):
    """
    下载指定依赖的源码
    
    DEPENDENCY: 依赖格式 group:artifact:version 或 group.artifact:version
    
    示例:
        download com.google.guava:guava:31.1-jre
        download com.google.gson:gson:2.8.9 -o ./sources
    """
    if not validate_dependency_format(dependency):
        click.echo(click.style("错误: 无效的依赖格式", fg='red'), err=True)
        click.echo("支持的格式: group:artifact:version 或 group.artifact:version")
        sys.exit(1)
    
    # 检查互斥选项
    if sources_only and force_binary:
        click.echo(click.style("错误: --sources-only 和 --force-binary 不能同时使用", fg='red'), err=True)
        sys.exit(1)
    
    if repositories and repo_names:
        click.echo(click.style("错误: --repositories 和 --repo-names 不能同时使用", fg='red'), err=True)
        sys.exit(1)
    
    # 初始化仓库管理器
    if repositories:
        repo_manager = RepositoryManager(repositories=list(repositories))
    elif repo_names:
        repo_manager = RepositoryManager(repository_names=list(repo_names))
    else:
        repo_manager = RepositoryManager()
    
    click.echo(f"正在下载依赖: {click.style(dependency, fg='cyan')}")
    
    # 创建进度跟踪器
    progress_tracker = ClickProgressTracker("下载源码")
    
    # 根据选项决定下载策略
    if force_binary:
        click.echo(click.style("强制下载二进制包进行反编译...", fg='yellow'))
    else:
        # 尝试下载源码
        sources_path = repo_manager.download_sources(dependency, output_dir, progress_tracker)
        
        if sources_path:
            click.echo(click.style(f"✓ 源码下载成功: {sources_path}", fg='green'))
            return
        
        if sources_only:
            click.echo(click.style("✗ 未找到源码 JAR，跳过反编译", fg='yellow'))
            sys.exit(1)
        
        # 如果没有源码，尝试下载并反编译二进制包
        click.echo(click.style("未找到源码 JAR，正在下载二进制包...", fg='yellow'))
    
    # 下载二进制包进行反编译
    
    binary_progress = ClickProgressTracker("下载二进制")
    binary_path = repo_manager.download_binary(dependency, output_dir, binary_progress)
    
    if not binary_path:
        click.echo(click.style("✗ 未找到二进制 JAR", fg='red'), err=True)
        sys.exit(1)
    
    # 反编译
    click.echo(click.style("正在反编译...", fg='yellow'))
    decompiler = JavaDecompiler()
    
    if not decompiler.check_java_available():
        click.echo(click.style("✗ 需要安装 Java 才能使用反编译功能", fg='red'), err=True)
        sys.exit(1)
    
    def decompile_progress(current, total, message):
        if message:
            click.echo(f"反编译进度: {message}")
    
    sources_path = decompiler.decompile_and_package(binary_path, output_dir, decompile_progress)
    
    if sources_path:
        click.echo(click.style(f"✓ 反编译完成: {sources_path}", fg='green'))
    else:
        click.echo(click.style("✗ 反编译失败", fg='red'), err=True)
        sys.exit(1)

@cli.command()
@click.argument('query')
@click.option('--max-results', '-n', default=10, help='最大结果数')
@click.pass_context
def search(ctx, query, max_results):
    """
    搜索 Maven 构件
    
    QUERY: 搜索关键词
    
    示例:
        search guava
        search "google gson" -n 5
    """
    repo_manager = RepositoryManager()
    
    click.echo(f"正在搜索: {click.style(query, fg='cyan')}")
    
    results = repo_manager.search_artifact(query, max_results)
    
    if not results:
        click.echo(click.style("未找到相关结果", fg='yellow'))
        return
    
    click.echo(f"\n找到 {len(results)} 个结果:\n")
    
    for i, result in enumerate(results, 1):
        group = result.get('group', '')
        artifact = result.get('artifact', '')
        version = result.get('version', '')
        description = result.get('description', '')
        
        click.echo(f"{i}. {click.style(f'{group}:{artifact}', fg='cyan', bold=True)}")
        click.echo(f"   版本: {click.style(version, fg='green')}")
        if description:
            click.echo(f"   描述: {description}")
        click.echo()

@cli.command()
@click.argument('dependency')
@click.pass_context
def versions(ctx, dependency):
    """
    列出依赖的可用版本
    
    DEPENDENCY: 依赖格式 group:artifact (不含版本)
    
    示例:
        versions com.google.guava:guava
        versions com.google.gson:gson
    """
    parts = dependency.split(':')
    if len(parts) != 2:
        click.echo(click.style("错误: 依赖格式应为 group:artifact", fg='red'), err=True)
        sys.exit(1)
    
    group, artifact = parts
    repo_manager = RepositoryManager()
    
    click.echo(f"正在查找 {click.style(dependency, fg='cyan')} 的可用版本...")
    
    versions_list = repo_manager.find_available_versions(group, artifact)
    
    if not versions_list:
        click.echo(click.style("未找到可用版本", fg='yellow'))
        return
    
    click.echo(f"\n找到 {len(versions_list)} 个版本:\n")
    
    for version in versions_list[:20]:  # 只显示前20个版本
        click.echo(f"  • {click.style(version, fg='green')}")
    
    if len(versions_list) > 20:
        click.echo(f"\n... 还有 {len(versions_list) - 20} 个版本")

@cli.command()
@click.argument('jar_path')
@click.option('--output-dir', '-o', default='decompiled', help='输出目录')
@click.pass_context
def decompile(ctx, jar_path, output_dir):
    """
    反编译 JAR 文件
    
    JAR_PATH: JAR 文件路径
    
    示例:
        decompile ./mylib.jar -o ./sources
    """
    if not os.path.exists(jar_path):
        click.echo(click.style(f"错误: 文件不存在 {jar_path}", fg='red'), err=True)
        sys.exit(1)
    
    decompiler = JavaDecompiler()
    
    if not decompiler.check_java_available():
        click.echo(click.style("✗ 需要安装 Java 才能使用反编译功能", fg='red'), err=True)
        sys.exit(1)
    
    click.echo(f"正在反编译: {click.style(jar_path, fg='cyan')}")
    
    def progress_callback(current, total, message):
        if message:
            click.echo(f"进度: {message}")
    
    success = decompiler.extract_sources_to_directory(jar_path, output_dir, progress_callback)
    
    if success:
        click.echo(click.style(f"✓ 反编译完成: {output_dir}", fg='green'))
    else:
        click.echo(click.style("✗ 反编译失败", fg='red'), err=True)
        sys.exit(1)

@cli.command()
@click.pass_context
def gui(ctx):
    """启动图形用户界面"""
    try:
        from .gui import launch_gui
        click.echo("正在启动图形界面...")
        launch_gui()
    except ImportError as e:
        click.echo(click.style(f"错误: 无法启动 GUI - {e}", fg='red'), err=True)
        click.echo("请确保安装了所有必要的依赖")
        sys.exit(1)

@cli.group()
def repo():
    """仓库管理命令"""
    pass

@repo.command()
def list():
    """列出所有配置的仓库"""
    repositories = config_manager.list_repositories()
    
    if not repositories:
        click.echo(click.style("没有配置任何仓库", fg='yellow'))
        return
    
    click.echo(f"配置的仓库 ({len(repositories)} 个):\n")
    
    for name, url in repositories.items():
        click.echo(f"  {click.style(name, fg='cyan', bold=True)}")
        click.echo(f"    {url}")
        click.echo()

@repo.command()
@click.argument('name')
@click.argument('url')
def add(name, url):
    """
    添加新仓库
    
    NAME: 仓库名称
    URL: 仓库URL
    
    示例:
        repo add my-repo https://my.repo.com/maven/
    """
    if config_manager.add_repository(name, url):
        click.echo(click.style(f"✓ 成功添加仓库: {name}", fg='green'))
    else:
        click.echo(click.style(f"✗ 添加仓库失败: {name}", fg='red'), err=True)
        sys.exit(1)

@repo.command()
@click.argument('name')
def remove(name):
    """
    删除仓库
    
    NAME: 仓库名称
    
    示例:
        repo remove my-repo
    """
    if config_manager.remove_repository(name):
        click.echo(click.style(f"✓ 成功删除仓库: {name}", fg='green'))
    else:
        click.echo(click.style(f"✗ 仓库不存在: {name}", fg='red'), err=True)
        sys.exit(1)

@repo.command()
@click.confirmation_option(prompt='确定要重置所有仓库配置吗？')
def reset():
    """重置仓库配置为默认值"""
    if config_manager.reset_to_defaults():
        click.echo(click.style("✓ 成功重置仓库配置", fg='green'))
    else:
        click.echo(click.style("✗ 重置配置失败", fg='red'), err=True)
        sys.exit(1)


@cli.command()
@click.option('--host', default='127.0.0.1', help='MCP 服务器绑定主机')
@click.option('--port', default=8000, type=int, help='MCP 服务器绑定端口')
@click.option('--stdio', is_flag=True, help='使用 STDIO 模式运行 MCP 服务器 (用于 Claude Desktop)')
def mcp(host, port, stdio):
    """启动 MCP (Model Context Protocol) 服务器
    
    这允许 AI 助手直接使用 Gradle File Downloader 工具。
    使用 --stdio 模式与 Claude Desktop 集成，或使用 HTTP 模式与其他客户端集成。
    
    示例:
        mcp --stdio                    # 用于 Claude Desktop
        mcp --host 0.0.0.0 --port 8080 # HTTP 服务器模式
    """
    try:
        from .mcp_server import mcp as mcp_server
        
        if stdio:
            click.echo("正在启动 MCP 服务器 (STDIO 模式)...")
            click.echo("此模式用于 Claude Desktop 集成。")
            click.echo("服务器现在等待来自 Claude Desktop 的连接...\n")
            mcp_server.run(transport="stdio")
        else:
            click.echo(f"正在启动 MCP 服务器: http://{host}:{port}")
            click.echo("可用的工具将在服务器启动后显示。")
            click.echo("按 Ctrl+C 停止服务器\n")
            mcp_server.run(transport="streamable-http", host=host, port=port)
    except ImportError as e:
        click.echo(click.style(f"错误: 无法启动 MCP 服务器 - {e}", fg='red'), err=True)
        click.echo("请确保安装了 fastmcp 依赖: pip install fastmcp")
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"MCP 服务器启动失败: {e}", fg='red'), err=True)
        sys.exit(1)


def main():
    """主入口函数"""
    cli() 