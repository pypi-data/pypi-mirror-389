"""异常定义模块"""


class SwaggerError(Exception):
    """Swagger SDK 基础异常类"""
    
    def __init__(self, message: str, **kwargs):
        """
        初始化异常
        
        Args:
            message: 错误消息
            **kwargs: 额外的错误信息
        """
        super().__init__(message)
        self.message = message
        for key, value in kwargs.items():
            setattr(self, key, value)


class ValidationError(SwaggerError):
    """验证错误"""
    
    def __init__(self, message: str, details: list = None, **kwargs):
        """
        初始化验证错误
        
        Args:
            message: 错误消息
            details: 详细错误列表
            **kwargs: 额外的错误信息
        """
        super().__init__(message, **kwargs)
        self.details = details or []


class ConfigurationError(SwaggerError):
    """配置错误"""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        """
        初始化配置错误
        
        Args:
            message: 错误消息
            config_key: 配置键名
            **kwargs: 额外的错误信息
        """
        super().__init__(message, **kwargs)
        self.config_key = config_key


class ScanError(SwaggerError):
    """扫描错误"""
    
    def __init__(self, message: str, module_path: str = None, **kwargs):
        """
        初始化扫描错误
        
        Args:
            message: 错误消息
            module_path: 模块路径
            **kwargs: 额外的错误信息
        """
        super().__init__(message, **kwargs)
        self.module_path = module_path


class ParseError(SwaggerError):
    """解析错误"""
    
    def __init__(self, message: str, source: str = None, **kwargs):
        """
        初始化解析错误
        
        Args:
            message: 错误消息
            source: 源信息（如类型、docstring等）
            **kwargs: 额外的错误信息
        """
        super().__init__(message, **kwargs)
        self.source = source

