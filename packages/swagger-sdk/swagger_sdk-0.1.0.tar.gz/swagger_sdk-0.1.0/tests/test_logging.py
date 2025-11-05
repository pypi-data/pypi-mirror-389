"""日志和调试功能测试"""

import unittest
import logging
import io
from swagger_sdk.logger import SwaggerLogger


class TestSwaggerLogger(unittest.TestCase):
    """日志和调试功能测试"""
    
    def test_logger_initialization(self):
        """测试日志器初始化"""
        logger = SwaggerLogger()
        
        self.assertIsNotNone(logger.logger)
        self.assertEqual(logger.logger.name, "swagger_sdk")
    
    def test_log_info(self):
        """测试输出 INFO 级别日志"""
        logger = SwaggerLogger()
        log_stream = io.StringIO()
        
        # 添加流处理器
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.INFO)
        logger.logger.addHandler(handler)
        logger.logger.setLevel(logging.INFO)
        
        logger.info("这是一条信息日志")
        
        log_output = log_stream.getvalue()
        self.assertIn("这是一条信息日志", log_output)
    
    def test_log_error(self):
        """测试输出 ERROR 级别日志"""
        logger = SwaggerLogger()
        log_stream = io.StringIO()
        
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.ERROR)
        logger.logger.addHandler(handler)
        logger.logger.setLevel(logging.ERROR)
        
        logger.error("这是一条错误日志")
        
        log_output = log_stream.getvalue()
        self.assertIn("这是一条错误日志", log_output)
    
    def test_debug_mode(self):
        """测试调试模式"""
        logger = SwaggerLogger(debug=True)
        
        self.assertEqual(logger.logger.level, logging.DEBUG)
    
    def test_log_warning(self):
        """测试输出 WARNING 级别日志"""
        logger = SwaggerLogger()
        log_stream = io.StringIO()
        
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.WARNING)
        logger.logger.addHandler(handler)
        logger.logger.setLevel(logging.WARNING)
        
        logger.warning("这是一条警告日志")
        
        log_output = log_stream.getvalue()
        self.assertIn("这是一条警告日志", log_output)

