"""
工具函数模块
包含日志配置、文件操作等通用功能
"""

import os
import logging
import sys
from typing import Callable, Any

def setup_logging(level: str = "INFO", log_file: str = None) -> None:
    """
    设置日志配置
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日志文件路径 (可选)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器 (如果指定了日志文件)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def format_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化的大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def create_progress_callback(update_func: Callable[[int, int, str], None]) -> Callable[[int, int], None]:
    """
    创建进度回调函数
    
    Args:
        update_func: 更新函数，接收 (current, total, message)
        
    Returns:
        进度回调函数
    """
    def callback(current: int, total: int):
        if total > 0:
            percentage = int((current / total) * 100)
            message = f"Downloaded {format_size(current)} / {format_size(total)} ({percentage}%)"
        else:
            message = f"Downloaded {format_size(current)}"
        
        update_func(current, total, message)
    
    return callback

def validate_dependency_format(dependency: str) -> bool:
    """
    验证依赖格式是否正确
    
    Args:
        dependency: 依赖字符串
        
    Returns:
        是否格式正确
    """
    if not dependency or not isinstance(dependency, str):
        return False
    
    # 支持两种格式：group:artifact:version 或 group.artifact:version
    parts = dependency.split(':')
    if len(parts) == 2:
        # group.artifact:version 格式
        group_artifact, version = parts
        return '.' in group_artifact and version.strip() != ''
    elif len(parts) == 3:
        # group:artifact:version 格式
        group, artifact, version = parts
        return all(part.strip() != '' for part in [group, artifact, version])
    
    return False

def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # Windows 非法字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    
    # 移除前后空格和点
    filename = filename.strip(' .')
    
    # 确保不为空
    if not filename:
        filename = "unnamed"
    
    return filename

def ensure_directory(path: str) -> None:
    """
    确保目录存在
    
    Args:
        path: 目录路径
    """
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, callback: Callable[[int, int, str], None] = None):
        self.callback = callback
        self.current = 0
        self.total = 0
        self.message = ""
    
    def update(self, current: int, total: int, message: str = ""):
        """更新进度"""
        self.current = current
        self.total = total
        self.message = message
        
        if self.callback:
            self.callback(current, total, message)
    
    def increment(self, amount: int = 1, message: str = ""):
        """增加进度"""
        self.update(self.current + amount, self.total, message)
    
    def set_total(self, total: int):
        """设置总数"""
        self.total = total
    
    def finish(self, message: str = "Completed"):
        """完成进度"""
        self.update(self.total, self.total, message) 