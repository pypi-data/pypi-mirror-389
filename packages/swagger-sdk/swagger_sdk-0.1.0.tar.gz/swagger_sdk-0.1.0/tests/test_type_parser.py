"""类型注解解析测试"""

import unittest
from typing import Optional, List, Dict
from swagger_sdk.type_parser import TypeParser
from swagger_sdk.enums import SchemaType


class TestTypeParser(unittest.TestCase):
    """类型注解解析器测试"""
    
    def test_parse_basic_types(self):
        """测试解析基本类型（int, str, bool）"""
        # 测试 int
        schema = TypeParser.parse_type(int)
        self.assertEqual(schema["type"], "integer")
        
        # 测试 str
        schema = TypeParser.parse_type(str)
        self.assertEqual(schema["type"], "string")
        
        # 测试 bool
        schema = TypeParser.parse_type(bool)
        self.assertEqual(schema["type"], "boolean")
        
        # 测试 float
        schema = TypeParser.parse_type(float)
        self.assertEqual(schema["type"], "number")
    
    def test_parse_optional_type(self):
        """测试解析 Optional 类型"""
        # 测试 Optional[int]
        schema = TypeParser.parse_type(Optional[int])
        self.assertEqual(schema["type"], "integer")
        # Optional 类型不应该标记为 required
        # 注意：这里我们只解析类型，required 标志在字段层面处理
        
        # 测试 Optional[str]
        schema = TypeParser.parse_type(Optional[str])
        self.assertEqual(schema["type"], "string")
    
    def test_parse_list_type(self):
        """测试解析 List 类型"""
        # 测试 List[int]
        schema = TypeParser.parse_type(List[int])
        self.assertEqual(schema["type"], "array")
        self.assertIn("items", schema)
        self.assertEqual(schema["items"]["type"], "integer")
        
        # 测试 List[str]
        schema = TypeParser.parse_type(List[str])
        self.assertEqual(schema["type"], "array")
        self.assertEqual(schema["items"]["type"], "string")
        
        # 测试 List[Optional[int]]
        schema = TypeParser.parse_type(List[Optional[int]])
        self.assertEqual(schema["type"], "array")
        self.assertEqual(schema["items"]["type"], "integer")
    
    def test_parse_dict_type(self):
        """测试解析 Dict 类型"""
        # 测试 Dict[str, int]
        schema = TypeParser.parse_type(Dict[str, int])
        self.assertEqual(schema["type"], "object")
        self.assertIn("additionalProperties", schema)
        self.assertEqual(schema["additionalProperties"]["type"], "integer")
        
        # 测试 Dict[str, str]
        schema = TypeParser.parse_type(Dict[str, str])
        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["additionalProperties"]["type"], "string")
    
    def test_parse_nested_types(self):
        """测试解析嵌套类型"""
        # 测试 List[List[int]]
        schema = TypeParser.parse_type(List[List[int]])
        self.assertEqual(schema["type"], "array")
        self.assertEqual(schema["items"]["type"], "array")
        self.assertEqual(schema["items"]["items"]["type"], "integer")
        
        # 测试 Dict[str, List[int]]
        schema = TypeParser.parse_type(Dict[str, List[int]])
        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["additionalProperties"]["type"], "array")
        self.assertEqual(schema["additionalProperties"]["items"]["type"], "integer")
    
    def test_parse_unknown_type(self):
        """测试解析未知类型（默认返回 string）"""
        # 测试未知类型
        schema = TypeParser.parse_type(object)
        self.assertEqual(schema["type"], "string")
        
        # 测试 None（应该返回 object）
        schema = TypeParser.parse_type(None)
        self.assertEqual(schema["type"], "object")

