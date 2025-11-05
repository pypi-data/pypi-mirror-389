"""兼容性测试"""

import unittest
import sys
import platform
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.enums import HttpMethod, ParamIn, SchemaType
from swagger_sdk.models import Parameter, Schema


class TestCompatibility(unittest.TestCase):
    """兼容性测试"""
    
    def test_python_version_compatibility(self):
        """测试 Python 版本兼容性"""
        # 检查 Python 版本
        version = sys.version_info
        self.assertGreaterEqual(
            version.major, 3,
            f"需要 Python 3.x，当前版本: {version.major}.{version.minor}"
        )
        self.assertGreaterEqual(
            version.minor, 8,
            f"需要 Python 3.8+，当前版本: {version.major}.{version.minor}"
        )
        print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    def test_platform_compatibility(self):
        """测试跨平台兼容性"""
        # 测试基本功能在不同平台上都能工作
        builder = SwaggerBuilder(
            title="兼容性测试",
            version="1.0.0"
        )
        
        builder.register_api(
            path="/api/test",
            method=HttpMethod.GET,
            summary="测试接口"
        )
        
        # 生成文档应该在不同平台都能工作
        json_doc = builder.generate_json()
        yaml_doc = builder.generate_yaml()
        html_doc = builder.generate_html()
        
        # 验证生成成功
        self.assertIn("openapi", json_doc)
        self.assertIn("openapi:", yaml_doc)
        self.assertIn("<!DOCTYPE html>", html_doc)
        
        print(f"平台: {platform.system()} {platform.release()}")
    
    def test_enum_string_compatibility(self):
        """测试枚举类的字符串兼容性"""
        # 测试枚举可以作为字符串使用
        method = HttpMethod.GET
        self.assertEqual(method.value, "GET")
        # 枚举继承自 str, Enum，所以可以直接比较
        self.assertEqual(method, "GET")
        
        param_in = ParamIn.QUERY
        self.assertEqual(param_in.value, "query")
        self.assertEqual(param_in, "query")
        
        schema_type = SchemaType.STRING
        self.assertEqual(schema_type.value, "string")
        self.assertEqual(schema_type, "string")
    
    def test_type_annotation_compatibility(self):
        """测试类型注解兼容性"""
        from typing import Optional, List, Dict
        
        # 测试 Optional
        builder = SwaggerBuilder(title="Test", version="1.0.0")
        builder.register_api(
            path="/api/test",
            method=HttpMethod.GET,
            summary="测试",
            parameters=[
                Parameter(
                    name="id",
                    param_type=Optional[int],
                    param_in=ParamIn.QUERY,
                    required=False
                )
            ]
        )
        
        # 应该能正常生成
        json_doc = builder.generate_json()
        self.assertIn("parameters", json_doc["paths"]["/api/test"]["get"])
    
    def test_unicode_compatibility(self):
        """测试 Unicode 字符兼容性"""
        builder = SwaggerBuilder(
            title="测试API",
            version="1.0.0",
            description="这是一个测试API，包含中文描述"
        )
        
        builder.register_api(
            path="/api/测试",
            method=HttpMethod.GET,
            summary="获取测试数据",
            description="这是一个包含中文的接口描述"
        )
        
        # 应该能正常处理 Unicode 字符
        json_doc = builder.generate_json()
        yaml_doc = builder.generate_yaml()
        html_doc = builder.generate_html()
        
        # 验证 Unicode 字符被正确处理
        json_str = str(json_doc)
        self.assertIn("测试", json_str)
        
        self.assertIn("测试", yaml_doc)
        self.assertIn("测试", html_doc)
    
    def test_dataclass_compatibility(self):
        """测试 dataclass 兼容性"""
        from dataclasses import dataclass
        
        @dataclass
        class TestModel:
            id: int
            name: str
        
        builder = SwaggerBuilder(title="Test", version="1.0.0")
        
        # 应该能正常解析 dataclass
        from swagger_sdk.dataclass_parser import DataclassParser
        schema = DataclassParser.parse_dataclass(TestModel)
        
        self.assertEqual(schema.schema_type, SchemaType.OBJECT)
        self.assertIn("id", schema.properties)
        self.assertIn("name", schema.properties)
    
    def test_import_compatibility(self):
        """测试导入兼容性"""
        # 测试所有主要模块都能正常导入
        try:
            from swagger_sdk import (
                SwaggerBuilder,
                ParamIn,
                HttpMethod,
                SchemaType,
                Parameter,
                Schema,
                swagger_api,
                swagger_controller,
                ConfigManager,
                SwaggerLogger,
                SwaggerError
            )
            # 如果导入成功，测试通过
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"导入失败: {e}")
    
    def test_file_encoding_compatibility(self):
        """测试文件编码兼容性"""
        import tempfile
        import os
        
        builder = SwaggerBuilder(
            title="编码测试",
            version="1.0.0",
            description="测试UTF-8编码"
        )
        builder.register_api(
            path="/api/test",
            method=HttpMethod.GET,
            summary="测试接口"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "test.json")
            yaml_path = os.path.join(tmpdir, "test.yaml")
            html_path = os.path.join(tmpdir, "test.html")
            
            # 应该能正常保存文件（UTF-8编码）
            builder.generate_json(output_path=json_path)
            builder.generate_yaml(output_path=yaml_path)
            builder.generate_html(output_path=html_path)
            
            # 验证文件存在
            self.assertTrue(os.path.exists(json_path))
            self.assertTrue(os.path.exists(yaml_path))
            self.assertTrue(os.path.exists(html_path))
            
            # 验证文件内容可以正确读取
            with open(json_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("编码测试", content)

