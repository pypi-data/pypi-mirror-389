"""
Nsc410 - 增强版表达式处理器
支持字符串处理、数学表达式求值和自定义函数调用
"""

from .core import Nsc410Processor, Ns4ev, set_compiler

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "Nsc410 表达式处理器，支持 Nsc371 注册的函数"

__all__ = [
    "Nsc410Processor",
    "Ns4ev", 
    "set_compiler"
]