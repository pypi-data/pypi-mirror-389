"""SwaggerBuilder 类测试"""

import unittest
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.models import Parameter, RequestBody, Response, ResponseContent, Schema
from swagger_sdk.enums import HttpMethod, ParamIn, SchemaType, ContentType


class TestSwaggerBuilder(unittest.TestCase):
    """SwaggerBuilder 类测试"""
    
    def test_builder_initialization(self):
        """测试 SwaggerBuilder 初始化"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        self.assertEqual(builder.title, "Test API")
        self.assertEqual(builder.version, "1.0.0")
        self.assertIsNotNone(builder.apis)
        self.assertEqual(len(builder.apis), 0)
    
    def test_builder_initialization_with_description(self):
        """测试带描述的初始化"""
        builder = SwaggerBuilder(
            title="Test API",
            version="1.0.0",
            description="测试API"
        )
        self.assertEqual(builder.description, "测试API")
    
    def test_register_api_basic(self):
        """测试基本接口注册"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表"
        )
        self.assertEqual(len(builder.apis), 1)
        api = builder.apis[0]
        self.assertEqual(api["path"], "/api/users")
        self.assertEqual(api["method"], HttpMethod.GET)
        self.assertEqual(api["summary"], "获取用户列表")
    
    def test_register_api_with_parameters(self):
        """测试注册带参数的接口"""
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
                    description="用户ID"
                )
            ]
        )
        api = builder.apis[0]
        self.assertIsNotNone(api.get("parameters"))
        self.assertEqual(len(api["parameters"]), 1)
        self.assertEqual(api["parameters"][0].name, "user_id")
    
    def test_register_api_with_responses(self):
        """测试注册带响应的接口"""
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
                        schema=Schema(schema_type=SchemaType.OBJECT)
                    )
                )
            }
        )
        api = builder.apis[0]
        self.assertIsNotNone(api.get("responses"))
        self.assertIn(200, api["responses"])
        self.assertEqual(api["responses"][200].description, "成功")
    
    def test_register_multiple_apis(self):
        """测试注册多个接口"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(path="/api/users", method=HttpMethod.GET, summary="获取用户")
        builder.register_api(path="/api/users", method=HttpMethod.POST, summary="创建用户")
        self.assertEqual(len(builder.apis), 2)
    
    def test_register_api_with_request_body(self):
        """测试注册带请求体的接口"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(
            path="/api/users",
            method=HttpMethod.POST,
            summary="创建用户",
            request_body=RequestBody(
                required=True,
                description="用户信息",
                schema=Schema(schema_type=SchemaType.OBJECT)
            )
        )
        api = builder.apis[0]
        self.assertIsNotNone(api.get("request_body"))
        self.assertTrue(api["request_body"].required)

