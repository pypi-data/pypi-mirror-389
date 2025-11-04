"""
MyPackage - 一个带有二进制保护的Python包
"""

__version__ = "0.1.0"
__author__ = "Your Name"

# 导入公共API
from .api import MyPackageAPI

# 导出主要接口
__all__ = ['MyPackageAPI']