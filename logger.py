"""
日志模块 - 支持控制台和文件双输出
"""
import logging
import sys
from datetime import datetime


def setup_logger(name: str = "serv00", log_file: str = None) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径（可选）
    
    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 日志格式
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件输出（如果指定）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class StatusPrinter:
    """
    状态打印辅助类，提供彩色输出
    """
    COLORS = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    
    @classmethod
    def success(cls, message: str) -> str:
        return f"{cls.COLORS['green']}✓{cls.COLORS['reset']} {message}"
    
    @classmethod
    def warning(cls, message: str) -> str:
        return f"{cls.COLORS['yellow']}⚠{cls.COLORS['reset']} {message}"
    
    @classmethod
    def error(cls, message: str) -> str:
        return f"{cls.COLORS['red']}✗{cls.COLORS['reset']} {message}"
    
    @classmethod
    def info(cls, message: str) -> str:
        return f"{cls.COLORS['blue']}ℹ{cls.COLORS['reset']} {message}"
