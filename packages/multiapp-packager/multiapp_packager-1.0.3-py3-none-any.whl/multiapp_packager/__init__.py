"""
多应用打包工具

一个基于配置文件的模块化多应用打包工具，用于将编译好的应用打包成多应用格式。
"""
try:
    from importlib.metadata import version
    __version__ = version("multiapp-packager")
except Exception:
    __version__ = "unknown"

__author__ = "Saw Xu"
__email__ = "saw1993@126.com"

from .app_info import AppInfo, ImageInfo
from .config_parser import ConfigParser
from .packager import Packager

__all__ = [
    "AppInfo",
    "ImageInfo",
    "ConfigParser",
    "Packager",
    "__version__",
]
