"""JSON 生成功能测试"""

import unittest
import json
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.models import Parameter, Response, ResponseContent, Schema
from swagger_sdk.enums import HttpMethod, ParamIn, SchemaType, ContentType


class TestJSONGenerator(unittest.TestCase):
    """JSON 生成功能测试"""
    
    def test_generate_basic_json(self):
        """测试生成基本的 OpenAPI 3.0 JSON"""
        builder = SwaggerBuilder(
            title="Test API",
            version="1.0.0",
            description="测试API"
        )
        result = builder.generate_json()
        
        # 验证基本结构
        self.assertIn("openapi", result)
        self.assertEqual(result["openapi"], "3.0.0")
        self.assertIn("info", result)
        self.assertEqual(result["info"]["title"], "Test API")
        self.assertEqual(result["info"]["version"], "1.0.0")
        self.assertEqual(result["info"]["description"], "测试API")
        self.assertIn("paths", result)
    
    def test_generate_json_with_paths(self):
        """测试生成包含路径的 JSON"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表"
        )
        
        result = builder.generate_json()
        
        self.assertIn("/api/users", result["paths"])
        self.assertIn("get", result["paths"]["/api/users"])
        operation = result["paths"]["/api/users"]["get"]
        self.assertEqual(operation["summary"], "获取用户列表")
    
    def test_generate_json_with_parameters(self):
        """测试生成包含参数的 JSON"""
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
        
        result = builder.generate_json()
        operation = result["paths"]["/api/users/{user_id}"]["get"]
        self.assertIn("parameters", operation)
        self.assertEqual(len(operation["parameters"]), 1)
        
        param = operation["parameters"][0]
        self.assertEqual(param["name"], "user_id")
        self.assertEqual(param["in"], "path")
        self.assertTrue(param["required"])
        self.assertEqual(param["description"], "用户ID")
        self.assertEqual(param["example"], 123)
        self.assertEqual(param["schema"]["type"], "integer")
    
    def test_generate_json_with_responses(self):
        """测试生成包含响应的 JSON"""
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
        
        result = builder.generate_json()
        operation = result["paths"]["/api/users"]["get"]
        self.assertIn("responses", operation)
        self.assertIn("200", operation["responses"])
        
        response = operation["responses"]["200"]
        self.assertEqual(response["description"], "成功")
        self.assertIn("content", response)
        self.assertIn("application/json", response["content"])
    
    def test_generate_json_multiple_paths(self):
        """测试生成多个路径的 JSON"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(path="/api/users", method=HttpMethod.GET, summary="获取用户")
        builder.register_api(path="/api/users", method=HttpMethod.POST, summary="创建用户")
        
        result = builder.generate_json()
        self.assertIn("/api/users", result["paths"])
        path = result["paths"]["/api/users"]
        self.assertIn("get", path)
        self.assertIn("post", path)
    
    def test_generate_json_save_to_file(self):
        """测试保存 JSON 到文件"""
        import tempfile
        import os
        
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(path="/api/users", method=HttpMethod.GET, summary="获取用户")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            result = builder.generate_json(output_path=temp_path)
            
            # 验证文件存在
            self.assertTrue(os.path.exists(temp_path))
            
            # 验证文件内容
            with open(temp_path, 'r', encoding='utf-8') as f:
                file_content = json.load(f)
            
            self.assertEqual(file_content["info"]["title"], "Test API")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

