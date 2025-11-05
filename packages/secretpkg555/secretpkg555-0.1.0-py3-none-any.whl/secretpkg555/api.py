"""
公共API接口
"""

from . import core_logic

class SecretAPI:
    """主要API类"""
    
    def __init__(self):
        self.version = "0.1.0"
    
    def process_data(self, data):
        """给数字加1"""
        return core_logic.secret_algorithm(data)
    
    def calculate(self, x, y):
        """简单加法"""
        return core_logic.complex_calculation(x, y)
    
    def get_info(self):
        """获取包信息"""
        return {
            "name": "SecretPkg555",
            "version": self.version,
            "description": "简单的1+1计算包"
        }