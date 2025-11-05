"""
SecretPkg555 - 简单的计算包
"""

__version__ = "0.1.0"

# 直接导出核心函数
from .core_logic import secret_algorithm, complex_calculation

__all__ = ['secret_algorithm', 'complex_calculation']