"""dataclass 模型解析测试"""

import unittest
from dataclasses import dataclass, field
from typing import List, Optional
from swagger_sdk.dataclass_parser import DataclassParser
from swagger_sdk.models import Schema
from swagger_sdk.enums import SchemaType, Format


class TestDataclassParser(unittest.TestCase):
    """dataclass 模型解析测试"""
    
    def test_parse_simple_dataclass(self):
        """测试解析简单的 dataclass"""
        @dataclass
        class User:
            id: int
            name: str
            email: str
        
        schema = DataclassParser.parse_dataclass(User)
        
        self.assertEqual(schema.schema_type, SchemaType.OBJECT)
        self.assertIsNotNone(schema.properties)
        self.assertIn("id", schema.properties)
        self.assertIn("name", schema.properties)
        self.assertIn("email", schema.properties)
        
        # 验证字段类型
        id_schema = schema.properties["id"]
        self.assertEqual(id_schema.schema_type, SchemaType.INTEGER)
        
        name_schema = schema.properties["name"]
        self.assertEqual(name_schema.schema_type, SchemaType.STRING)
        
        email_schema = schema.properties["email"]
        self.assertEqual(email_schema.schema_type, SchemaType.STRING)
        
        # 验证必填字段
        self.assertIsNotNone(schema.required)
        self.assertIn("id", schema.required)
        self.assertIn("name", schema.required)
        self.assertIn("email", schema.required)
    
    def test_parse_dataclass_with_optional_fields(self):
        """测试解析包含可选字段的 dataclass"""
        @dataclass
        class User:
            id: int
            name: str
            age: Optional[int] = None
            email: Optional[str] = None
        
        schema = DataclassParser.parse_dataclass(User)
        
        # 必填字段
        self.assertIsNotNone(schema.required)
        self.assertIn("id", schema.required)
        self.assertIn("name", schema.required)
        
        # 可选字段不应该在 required 中
        if schema.required:
            self.assertNotIn("age", schema.required)
            self.assertNotIn("email", schema.required)
        
        # 可选字段应该有默认值
        age_schema = schema.properties["age"]
        self.assertEqual(age_schema.default, None)
    
    def test_parse_dataclass_with_field_defaults(self):
        """测试解析包含默认值的 dataclass"""
        @dataclass
        class User:
            id: int
            name: str
            status: str = "active"
            score: float = 0.0
        
        schema = DataclassParser.parse_dataclass(User)
        
        # 有默认值的字段不应该在 required 中
        if schema.required:
            self.assertNotIn("status", schema.required)
            self.assertNotIn("score", schema.required)
        
        # 验证默认值
        status_schema = schema.properties["status"]
        self.assertEqual(status_schema.default, "active")
        
        score_schema = schema.properties["score"]
        self.assertEqual(score_schema.default, 0.0)
    
    def test_parse_dataclass_with_field_metadata(self):
        """测试解析包含 Field 元数据的 dataclass"""
        from swagger_sdk.models import Field
        
        @dataclass
        class User:
            id: int = Field(description="用户ID", example=1)
            name: str = Field(description="用户名", min_length=3, max_length=20)
            email: str = Field(description="邮箱", format=Format.EMAIL)
        
        schema = DataclassParser.parse_dataclass(User)
        
        # 验证字段描述
        id_schema = schema.properties["id"]
        self.assertEqual(id_schema.description, "用户ID")
        self.assertEqual(id_schema.example, 1)
        
        name_schema = schema.properties["name"]
        self.assertEqual(name_schema.description, "用户名")
        self.assertEqual(name_schema.min_length, 3)
        self.assertEqual(name_schema.max_length, 20)
        
        email_schema = schema.properties["email"]
        self.assertEqual(email_schema.description, "邮箱")
        self.assertEqual(email_schema.format, Format.EMAIL)
    
    def test_parse_nested_dataclass(self):
        """测试解析嵌套的 dataclass"""
        @dataclass
        class Address:
            street: str
            city: str
            zip_code: str
        
        @dataclass
        class User:
            id: int
            name: str
            address: Address
        
        schema = DataclassParser.parse_dataclass(User)
        
        # 验证嵌套对象
        address_schema = schema.properties["address"]
        self.assertEqual(address_schema.schema_type, SchemaType.OBJECT)
        self.assertIsNotNone(address_schema.properties)
        self.assertIn("street", address_schema.properties)
        self.assertIn("city", address_schema.properties)
        self.assertIn("zip_code", address_schema.properties)
    
    def test_parse_dataclass_with_list_fields(self):
        """测试解析包含列表字段的 dataclass"""
        @dataclass
        class User:
            id: int
            name: str
            tags: List[str]
            scores: List[int] = field(default_factory=list)
        
        schema = DataclassParser.parse_dataclass(User)
        
        # 验证列表字段
        tags_schema = schema.properties["tags"]
        self.assertEqual(tags_schema.schema_type, SchemaType.ARRAY)
        self.assertIsNotNone(tags_schema.items)
        self.assertEqual(tags_schema.items.schema_type, SchemaType.STRING)
        
        scores_schema = schema.properties["scores"]
        self.assertEqual(scores_schema.schema_type, SchemaType.ARRAY)
        self.assertIsNotNone(scores_schema.items)
        self.assertEqual(scores_schema.items.schema_type, SchemaType.INTEGER)

