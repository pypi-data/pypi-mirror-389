"""基础类测试"""

import unittest
from swagger_sdk.models import (
    Parameter, Field, Schema, RequestBody, ResponseContent, Response
)
from swagger_sdk.enums import ParamIn, Format, SchemaType, ContentType


class TestParameter(unittest.TestCase):
    """Parameter 类测试"""
    
    def test_parameter_creation(self):
        """测试创建 Parameter 实例"""
        param = Parameter(
            name="user_id",
            param_type=int,
            param_in=ParamIn.PATH,
            required=True,
            description="用户ID",
            example=123
        )
        self.assertEqual(param.name, "user_id")
        self.assertEqual(param.param_type, int)
        self.assertEqual(param.param_in, ParamIn.PATH)
        self.assertTrue(param.required)
        self.assertEqual(param.description, "用户ID")
        self.assertEqual(param.example, 123)
    
    def test_parameter_defaults(self):
        """测试 Parameter 默认值"""
        param = Parameter(name="page", param_type=int)
        self.assertEqual(param.param_in, ParamIn.QUERY)
        self.assertTrue(param.required)
        self.assertIsNone(param.description)
        self.assertIsNone(param.example)
    
    def test_parameter_with_format(self):
        """测试 Parameter 带格式"""
        param = Parameter(
            name="email",
            param_type=str,
            format=Format.EMAIL
        )
        self.assertEqual(param.format, Format.EMAIL)


class TestField(unittest.TestCase):
    """Field 类测试"""
    
    def test_field_creation(self):
        """测试创建 Field 实例"""
        field = Field(
            description="用户名",
            example="zhangsan",
            required=True,
            min_length=3,
            max_length=20
        )
        self.assertEqual(field.description, "用户名")
        self.assertEqual(field.example, "zhangsan")
        self.assertTrue(field.required)
        self.assertEqual(field.min_length, 3)
        self.assertEqual(field.max_length, 20)
    
    def test_field_defaults(self):
        """测试 Field 默认值"""
        field = Field()
        self.assertTrue(field.required)
        self.assertIsNone(field.description)
        self.assertIsNone(field.example)


class TestSchema(unittest.TestCase):
    """Schema 类测试"""
    
    def test_schema_creation(self):
        """测试创建 Schema 实例"""
        schema = Schema(
            schema_type=SchemaType.STRING,
            description="用户名",
            example="zhangsan"
        )
        self.assertEqual(schema.schema_type, SchemaType.STRING)
        self.assertEqual(schema.description, "用户名")
        self.assertEqual(schema.example, "zhangsan")
    
    def test_schema_with_properties(self):
        """测试带属性的 Schema"""
        schema = Schema(
            schema_type=SchemaType.OBJECT,
            properties={
                "id": Schema(schema_type=SchemaType.INTEGER),
                "name": Schema(schema_type=SchemaType.STRING)
            },
            required=["id", "name"]
        )
        self.assertEqual(schema.schema_type, SchemaType.OBJECT)
        self.assertIsNotNone(schema.properties)
        self.assertEqual(len(schema.properties), 2)
        self.assertEqual(schema.required, ["id", "name"])
    
    def test_schema_array_with_items(self):
        """测试数组类型的 Schema"""
        schema = Schema(
            schema_type=SchemaType.ARRAY,
            items=Schema(schema_type=SchemaType.STRING)
        )
        self.assertEqual(schema.schema_type, SchemaType.ARRAY)
        self.assertIsNotNone(schema.items)
        self.assertEqual(schema.items.schema_type, SchemaType.STRING)


class TestRequestBody(unittest.TestCase):
    """RequestBody 类测试"""
    
    def test_request_body_creation(self):
        """测试创建 RequestBody 实例"""
        body = RequestBody(
            required=True,
            description="用户信息",
            content_type=ContentType.JSON
        )
        self.assertTrue(body.required)
        self.assertEqual(body.description, "用户信息")
        self.assertEqual(body.content_type, ContentType.JSON)
    
    def test_request_body_defaults(self):
        """测试 RequestBody 默认值"""
        body = RequestBody()
        self.assertTrue(body.required)
        self.assertEqual(body.content_type, ContentType.JSON)
        self.assertIsNone(body.schema)
        self.assertIsNone(body.model)


class TestResponseContent(unittest.TestCase):
    """ResponseContent 类测试"""
    
    def test_response_content_creation(self):
        """测试创建 ResponseContent 实例"""
        content = ResponseContent(
            content_type=ContentType.JSON,
            schema=Schema(schema_type=SchemaType.OBJECT)
        )
        self.assertEqual(content.content_type, ContentType.JSON)
        self.assertIsNotNone(content.schema)
    
    def test_response_content_defaults(self):
        """测试 ResponseContent 默认值"""
        content = ResponseContent()
        self.assertEqual(content.content_type, ContentType.JSON)
        self.assertIsNone(content.schema)
        self.assertIsNone(content.model)


class TestResponse(unittest.TestCase):
    """Response 类测试"""
    
    def test_response_creation(self):
        """测试创建 Response 实例"""
        response = Response(
            description="成功",
            content=ResponseContent()
        )
        self.assertEqual(response.description, "成功")
        self.assertIsNotNone(response.content)
    
    def test_response_without_content(self):
        """测试没有内容的 Response"""
        response = Response(description="未授权")
        self.assertEqual(response.description, "未授权")
        self.assertIsNone(response.content)

