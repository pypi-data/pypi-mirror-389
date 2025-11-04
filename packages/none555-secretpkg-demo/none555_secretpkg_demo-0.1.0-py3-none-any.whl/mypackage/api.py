"""
公共API接口 - 这个文件会保持源码形式
"""

try:
    # 尝试导入编译后的核心模块
    from . import core_logic
except ImportError:
    # 如果编译版本不存在，回退到源码版本（开发时使用）
    from . import core_logic

class MyPackageAPI:
    """
    MyPackage的主要API接口
    """
    
    def __init__(self):
        """初始化API"""
        self.version = "0.1.0"
    
    def process_data(self, data):
        """
        处理数据的公共接口 - 给数字加1
        
        Args:
            data: 要处理的数据
            
        Returns:
            处理后的结果
        """
        return core_logic.secret_algorithm(data)
    
    def calculate(self, x, y):
        """
        计算接口 - 简单加法
        
        Args:
            x: 第一个数字
            y: 第二个数字
            
        Returns:
            计算结果
        """
        return core_logic.complex_calculation(x, y)
    
    def get_info(self):
        """
        获取包信息
        
        Returns:
            包的基本信息
        """
        return {
            "name": "MyPackage",
            "version": self.version,
            "description": "一个简单的1+1计算包",
            "core_module_compiled": hasattr(core_logic, '__loader__') and 
                                  'nuitka' in str(type(core_logic.__loader__)).lower()
        }