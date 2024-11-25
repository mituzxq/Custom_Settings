"""
工具模块，包含配置管理和通用工具函数
"""

from .config import (
    Config, 
    DARK_THEME, 
    LIGHT_THEME,
    save_config,
    load_config,
    DEFAULT_CONFIG
)
from .utils import (
    setup_logging, 
    cleanup_old_logs, 
    safe_destroy,
    global_exception_handler
)

import os
import sys

def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        # PyInstaller创建临时文件夹,将路径存储在_MEIPASS中
        base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        return os.path.join(base_path, relative_path)
    except Exception:
        return os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), relative_path)

__all__ = [
    'Config',
    'DARK_THEME',
    'LIGHT_THEME',
    'save_config',
    'load_config',
    'DEFAULT_CONFIG',
    'setup_logging',
    'cleanup_old_logs',
    'safe_destroy',
    'global_exception_handler'
]
