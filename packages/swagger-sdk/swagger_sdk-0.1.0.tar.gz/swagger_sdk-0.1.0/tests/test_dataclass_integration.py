"""dataclass 集成测试"""

import unittest
from dataclasses import dataclass
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.models import RequestBody, Response, ResponseContent
from swagger_sdk.enums import HttpMethod, ContentType


class TestDataclassIntegration(unittest.TestCase):
    """dataclass 集成测试"""
    
    def test_request_body_with_dataclass_model(self):
        """测试请求体使用 dataclass 模型"""
        @dataclass
        class UserCreate:
            username: str
            email: str
            age: int = 0
        
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(
            path="/api/users",
            method=HttpMethod.POST,
            summary="创建用户",
            request_body=RequestBody(
                required=True,
                description="用户信息",
                model=UserCreate
            )
        )
        
        json_doc = builder.generate_json()
        
        # 验证请求体包含 dataclass 的 schema
        request_body = json_doc["paths"]["/api/users"]["post"]["requestBody"]
        self.assertTrue(request_body["required"])
        
        schema = request_body["content"]["application/json"]["schema"]
        self.assertEqual(schema["type"], "object")
        self.assertIn("properties", schema)
        self.assertIn("username", schema["properties"])
        self.assertIn("email", schema["properties"])
        self.assertIn("age", schema["properties"])
        
        # 验证必填字段
        self.assertIn("username", schema["required"])
        self.assertIn("email", schema["required"])
        self.assertNotIn("age", schema["required"])
    
    def test_response_with_dataclass_model(self):
        """测试响应使用 dataclass 模型"""
        @dataclass
        class UserInfo:
            id: int
            username: str
            email: str
        
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(
            path="/api/users/{user_id}",
            method=HttpMethod.GET,
            summary="获取用户详情",
            responses={
                200: Response(
                    description="成功",
                    content=ResponseContent(
                        content_type=ContentType.JSON,
                        model=UserInfo
                    )
                )
            }
        )
        
        json_doc = builder.generate_json()
        
        # 验证响应包含 dataclass 的 schema
        response = json_doc["paths"]["/api/users/{user_id}"]["get"]["responses"]["200"]
        schema = response["content"]["application/json"]["schema"]
        
        self.assertEqual(schema["type"], "object")
        self.assertIn("properties", schema)
        self.assertIn("id", schema["properties"])
        self.assertIn("username", schema["properties"])
        self.assertIn("email", schema["properties"])

