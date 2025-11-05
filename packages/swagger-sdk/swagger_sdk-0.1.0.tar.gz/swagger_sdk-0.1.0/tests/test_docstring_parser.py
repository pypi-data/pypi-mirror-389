"""文档字符串解析测试"""

import unittest
from swagger_sdk.docstring_parser import DocstringParser


class TestDocstringParser(unittest.TestCase):
    """文档字符串解析器测试"""
    
    def test_parse_google_style_docstring(self):
        """测试解析 Google 风格 docstring"""
        docstring = """
        获取用户列表
        
        Args:
            page: 页码，从1开始
            size: 每页数量，默认10
        
        Returns:
            用户列表和总数
        """
        
        result = DocstringParser.parse(docstring)
        
        self.assertEqual(result["summary"], "获取用户列表")
        self.assertIn("Args", result)
        self.assertIn("page", result["Args"])
        self.assertEqual(result["Args"]["page"], "页码，从1开始")
        self.assertIn("size", result["Args"])
        self.assertEqual(result["Args"]["size"], "每页数量，默认10")
        self.assertIn("Returns", result)
        self.assertEqual(result["Returns"], "用户列表和总数")
    
    def test_parse_google_style_with_multiple_params(self):
        """测试解析多个参数的 Google 风格 docstring"""
        docstring = """
        创建用户
        
        Args:
            username: 用户名，3-20个字符
            email: 邮箱地址
            age: 年龄，可选
        
        Returns:
            创建的用户信息
        """
        
        result = DocstringParser.parse(docstring)
        
        self.assertEqual(result["summary"], "创建用户")
        self.assertEqual(len(result["Args"]), 3)
        self.assertEqual(result["Args"]["username"], "用户名，3-20个字符")
        self.assertEqual(result["Args"]["email"], "邮箱地址")
        self.assertEqual(result["Args"]["age"], "年龄，可选")
    
    def test_parse_simple_docstring(self):
        """测试解析简单 docstring（只有摘要）"""
        docstring = "获取用户列表"
        
        result = DocstringParser.parse(docstring)
        
        self.assertEqual(result["summary"], "获取用户列表")
        # Args 和 Returns 字段总是存在，但为空
        self.assertEqual(result["Args"], {})
        self.assertEqual(result["Returns"], "")
    
    def test_parse_docstring_with_returns_only(self):
        """测试解析只有返回值的 docstring"""
        docstring = """
        获取用户信息
        
        Returns:
            用户信息字典
        """
        
        result = DocstringParser.parse(docstring)
        
        self.assertEqual(result["summary"], "获取用户信息")
        self.assertIn("Returns", result)
        self.assertEqual(result["Returns"], "用户信息字典")
    
    def test_parse_empty_docstring(self):
        """测试解析空 docstring"""
        result = DocstringParser.parse("")
        self.assertEqual(result["summary"], "")
        
        result = DocstringParser.parse(None)
        self.assertEqual(result["summary"], "")
    
    def test_parse_multiline_summary(self):
        """测试解析多行摘要"""
        docstring = """
        这是一个很长的摘要
        可能会跨多行
        但应该只取第一行
        
        Args:
            param1: 参数1
        """
        
        result = DocstringParser.parse(docstring)
        # 多行摘要应该合并或只取第一行
        self.assertIn("这是一个很长的摘要", result["summary"])

