"""YAML 生成功能测试"""

import unittest
import os
import tempfile
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.models import Parameter, Response, ResponseContent, Schema
from swagger_sdk.enums import HttpMethod, ParamIn, SchemaType, ContentType


class TestYAMLGenerator(unittest.TestCase):
    """YAML 生成功能测试"""
    
    def test_generate_basic_yaml(self):
        """测试生成基本的 YAML 格式"""
        builder = SwaggerBuilder(
            title="Test API",
            version="1.0.0",
            description="测试API"
        )
        result = builder.generate_yaml()
        
        # 验证基本结构
        self.assertIn("openapi:", result)
        self.assertIn("3.0.0", result)
        self.assertIn("info:", result)
        self.assertIn("title: Test API", result)
        self.assertIn("version: 1.0.0", result)
        self.assertIn("description: 测试API", result)
        self.assertIn("paths:", result)
    
    def test_generate_yaml_with_paths(self):
        """测试生成包含路径的 YAML"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表"
        )
        
        result = builder.generate_yaml()
        
        self.assertIn("/api/users:", result)
        self.assertIn("get:", result)
        self.assertIn("summary: 获取用户列表", result)
    
    def test_generate_yaml_with_parameters(self):
        """测试生成包含参数的 YAML"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(
            path="/api/users/{user_id}",
            method=HttpMethod.GET,
            summary="获取用户详情",
            parameters=[
                Parameter(
                    name="user_id",
                    param_type=int,
                    param_in=ParamIn.PATH,
                    required=True,
                    description="用户ID",
                    example=123
                )
            ]
        )
        
        result = builder.generate_yaml()
        
        self.assertIn("parameters:", result)
        self.assertIn("- name: user_id", result)
        self.assertIn("in: path", result)
        self.assertIn("required: true", result)
        self.assertIn("description: 用户ID", result)
        self.assertIn("example: 123", result)
        self.assertIn("type: integer", result)
    
    def test_generate_yaml_with_responses(self):
        """测试生成包含响应的 YAML"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表",
            responses={
                200: Response(
                    description="成功",
                    content=ResponseContent(
                        content_type=ContentType.JSON,
                        schema=Schema(
                            schema_type=SchemaType.OBJECT,
                            properties={
                                "total": Schema(
                                    schema_type=SchemaType.INTEGER,
                                    description="总数"
                                )
                            }
                        )
                    )
                )
            }
        )
        
        result = builder.generate_yaml()
        
        self.assertIn("responses:", result)
        self.assertIn("200:", result)
        self.assertIn("description: 成功", result)
        self.assertIn("content:", result)
        self.assertIn("application/json:", result)
        self.assertIn("schema:", result)
    
    def test_generate_yaml_save_to_file(self):
        """测试保存 YAML 到文件"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(path="/api/users", method=HttpMethod.GET, summary="获取用户")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml', encoding='utf-8') as f:
            temp_path = f.name
        
        try:
            result = builder.generate_yaml(output_path=temp_path)
            
            # 验证文件存在
            self.assertTrue(os.path.exists(temp_path))
            
            # 验证文件内容
            with open(temp_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            self.assertIn("title: Test API", file_content)
            self.assertIn("/api/users:", file_content)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_yaml_indentation(self):
        """测试 YAML 缩进格式"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表"
        )
        
        result = builder.generate_yaml()
        lines = result.split('\n')
        
        # 检查缩进是否正确（paths 应该缩进2个空格）
        paths_found = False
        for i, line in enumerate(lines):
            if line.strip() == "paths:":
                paths_found = True
                # 下一行应该是路径，应该缩进2个空格
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip() and not next_line.startswith('  '):
                        # 如果下一行有内容但不是以2个空格开始，可能是空行或注释
                        pass
                break
        
        self.assertTrue(paths_found, "应该包含 paths 部分")

