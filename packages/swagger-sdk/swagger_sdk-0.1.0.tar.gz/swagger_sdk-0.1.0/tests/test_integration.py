"""集成测试 - 完整流程测试"""

import unittest
import tempfile
import os
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.models import Parameter, RequestBody, Response, ResponseContent, Schema
from swagger_sdk.enums import HttpMethod, ParamIn, SchemaType, ContentType
from dataclasses import dataclass


class TestIntegration(unittest.TestCase):
    """集成测试 - 完整流程测试"""
    
    def test_complete_workflow(self):
        """测试完整的工作流程：注册 -> 扫描 -> 生成 -> 验证"""
        # 1. 创建构建器
        builder = SwaggerBuilder(
            title="集成测试API",
            version="1.0.0",
            description="完整流程测试"
        )
        
        # 2. 手动注册接口
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表",
            parameters=[
                Parameter(
                    name="page",
                    param_type=int,
                    param_in=ParamIn.QUERY,
                    required=False,
                    default=1,
                    description="页码"
                )
            ],
            responses={
                200: Response(
                    description="成功",
                    content=ResponseContent(
                        content_type=ContentType.JSON,
                        schema=Schema(
                            schema_type=SchemaType.OBJECT,
                            properties={
                                "total": Schema(schema_type=SchemaType.INTEGER),
                                "users": Schema(
                                    schema_type=SchemaType.ARRAY,
                                    items=Schema(schema_type=SchemaType.OBJECT)
                                )
                            }
                        )
                    )
                )
            }
        )
        
        # 3. 注册组件
        user_schema = Schema(
            schema_type=SchemaType.OBJECT,
            properties={
                "id": Schema(schema_type=SchemaType.INTEGER),
                "name": Schema(schema_type=SchemaType.STRING)
            },
            required=["id", "name"]
        )
        builder.register_component_schema("User", user_schema)
        
        # 4. 验证文档
        is_valid, errors = builder.validate()
        self.assertTrue(is_valid, f"验证失败: {errors}")
        
        # 5. 生成 JSON
        json_doc = builder.generate_json()
        self.assertIn("openapi", json_doc)
        self.assertIn("3.0.0", json_doc["openapi"])
        self.assertIn("paths", json_doc)
        self.assertIn("/api/users", json_doc["paths"])
        
        # 6. 生成 YAML
        yaml_doc = builder.generate_yaml()
        self.assertIn("openapi:", yaml_doc)
        self.assertIn("/api/users:", yaml_doc)
        
        # 7. 生成 HTML
        html_doc = builder.generate_html()
        self.assertIn("<!DOCTYPE html>", html_doc)
        self.assertIn("集成测试API", html_doc)
    
    def test_dataclass_workflow(self):
        """测试 dataclass 工作流程"""
        @dataclass
        class UserCreate:
            username: str
            email: str
            age: int = 0
        
        @dataclass
        class UserResponse:
            id: int
            username: str
            email: str
        
        builder = SwaggerBuilder(title="Dataclass API", version="1.0.0")
        
        # 使用 dataclass 作为请求体和响应
        builder.register_api(
            path="/api/users",
            method=HttpMethod.POST,
            summary="创建用户",
            request_body=RequestBody(
                required=True,
                model=UserCreate
            ),
            responses={
                200: Response(
                    description="成功",
                    content=ResponseContent(
                        content_type=ContentType.JSON,
                        model=UserResponse
                    )
                )
            }
        )
        
        # 生成 JSON
        json_doc = builder.generate_json()
        
        # 验证请求体包含 dataclass schema
        request_body = json_doc["paths"]["/api/users"]["post"]["requestBody"]
        schema = request_body["content"]["application/json"]["schema"]
        self.assertIn("properties", schema)
        self.assertIn("username", schema["properties"])
        self.assertIn("email", schema["properties"])
        
        # 验证响应包含 dataclass schema
        response = json_doc["paths"]["/api/users"]["post"]["responses"]["200"]
        response_schema = response["content"]["application/json"]["schema"]
        self.assertIn("properties", response_schema)
        self.assertIn("id", response_schema["properties"])
    
    def test_batch_register_and_update(self):
        """测试批量注册和更新"""
        builder = SwaggerBuilder(title="Batch API", version="1.0.0")
        
        # 批量注册
        apis = [
            {
                "path": "/api/users",
                "method": HttpMethod.GET,
                "summary": "获取用户列表"
            },
            {
                "path": "/api/users/{id}",
                "method": HttpMethod.GET,
                "summary": "获取用户详情"
            }
        ]
        builder.register_apis(apis)
        
        self.assertEqual(len(builder.apis), 2)
        
        # 更新接口
        builder.update_api(
            path="/api/users",
            method=HttpMethod.GET,
            description="获取所有用户的列表"
        )
        
        # 验证更新
        api = builder.apis[0]
        self.assertEqual(api["summary"], "获取用户列表")
        self.assertEqual(api["description"], "获取所有用户的列表")
    
    def test_file_output(self):
        """测试文件输出功能"""
        builder = SwaggerBuilder(title="File API", version="1.0.0")
        builder.register_api(
            path="/api/test",
            method=HttpMethod.GET,
            summary="测试接口"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "api.json")
            yaml_path = os.path.join(tmpdir, "api.yaml")
            html_path = os.path.join(tmpdir, "api.html")
            
            # 生成文件
            builder.generate_json(output_path=json_path)
            builder.generate_yaml(output_path=yaml_path)
            builder.generate_html(output_path=html_path)
            
            # 验证文件存在
            self.assertTrue(os.path.exists(json_path))
            self.assertTrue(os.path.exists(yaml_path))
            self.assertTrue(os.path.exists(html_path))
            
            # 验证文件内容
            with open(json_path, 'r', encoding='utf-8') as f:
                json_content = f.read()
                self.assertIn("File API", json_content)
            
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
                self.assertIn("File API", yaml_content)
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                self.assertIn("File API", html_content)

