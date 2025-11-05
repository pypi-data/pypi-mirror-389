"""错误处理增强测试"""

import unittest
from swagger_sdk.exceptions import (
    SwaggerError,
    ValidationError,
    ConfigurationError,
    ScanError
)


class TestExceptions(unittest.TestCase):
    """错误处理增强测试"""
    
    def test_swagger_error_base(self):
        """测试基础 SwaggerError"""
        error = SwaggerError("基础错误")
        
        self.assertEqual(str(error), "基础错误")
        self.assertIsInstance(error, Exception)
    
    def test_validation_error(self):
        """测试 ValidationError"""
        error = ValidationError("验证失败", details=["字段1无效", "字段2缺失"])
        
        self.assertEqual(str(error), "验证失败")
        self.assertEqual(error.details, ["字段1无效", "字段2缺失"])
        self.assertIsInstance(error, SwaggerError)
    
    def test_configuration_error(self):
        """测试 ConfigurationError"""
        error = ConfigurationError("配置错误", config_key="missing_key")
        
        self.assertEqual(str(error), "配置错误")
        self.assertEqual(error.config_key, "missing_key")
        self.assertIsInstance(error, SwaggerError)
    
    def test_scan_error(self):
        """测试 ScanError"""
        error = ScanError("扫描失败", module_path="test_module")
        
        self.assertEqual(str(error), "扫描失败")
        self.assertEqual(error.module_path, "test_module")
        self.assertIsInstance(error, SwaggerError)
    
    def test_error_with_details(self):
        """测试带详细信息的错误"""
        error = ValidationError(
            "验证失败",
            details=["错误1", "错误2"],
            field="user_id"
        )
        
        self.assertEqual(len(error.details), 2)
        self.assertEqual(error.field, "user_id")

