"""日志模块"""

import logging
from typing import Optional


class SwaggerLogger:
    """Swagger SDK 日志器"""
    
    def __init__(self, debug: bool = False, name: str = "swagger_sdk"):
        """
        初始化日志器
        
        Args:
            debug: 是否启用调试模式
            name: 日志器名称
        """
        self.logger = logging.getLogger(name)
        
        # 如果还没有处理器，添加一个默认的控制台处理器
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # 设置日志级别
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
    
    def debug(self, message: str, *args, **kwargs):
        """输出 DEBUG 级别日志"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """输出 INFO 级别日志"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """输出 WARNING 级别日志"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """输出 ERROR 级别日志"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """输出 CRITICAL 级别日志"""
        self.logger.critical(message, *args, **kwargs)

