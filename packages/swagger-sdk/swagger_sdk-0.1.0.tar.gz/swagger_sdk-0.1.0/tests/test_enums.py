"""枚举类测试"""

import unittest
from swagger_sdk.enums import ParamIn, HttpMethod, SchemaType, Format, ContentType


class TestParamIn(unittest.TestCase):
    """ParamIn 枚举测试"""
    
    def test_param_in_values(self):
        """测试参数位置枚举值"""
        self.assertEqual(ParamIn.QUERY, "query")
        self.assertEqual(ParamIn.PATH, "path")
        self.assertEqual(ParamIn.HEADER, "header")
        self.assertEqual(ParamIn.COOKIE, "cookie")
    
    def test_param_in_string_compatibility(self):
        """测试枚举可以作为字符串使用"""
        # 枚举值本身等于字符串
        self.assertEqual(ParamIn.QUERY, "query")
        # 枚举成员是字符串类型
        self.assertTrue(isinstance(ParamIn.QUERY.value, str))
        # 可以直接比较
        param = ParamIn.QUERY
        self.assertEqual(param, "query")


class TestHttpMethod(unittest.TestCase):
    """HttpMethod 枚举测试"""
    
    def test_http_method_values(self):
        """测试 HTTP 方法枚举值"""
        self.assertEqual(HttpMethod.GET, "GET")
        self.assertEqual(HttpMethod.POST, "POST")
        self.assertEqual(HttpMethod.PUT, "PUT")
        self.assertEqual(HttpMethod.DELETE, "DELETE")
        self.assertEqual(HttpMethod.PATCH, "PATCH")
        self.assertEqual(HttpMethod.HEAD, "HEAD")
        self.assertEqual(HttpMethod.OPTIONS, "OPTIONS")
        self.assertEqual(HttpMethod.TRACE, "TRACE")
    
    def test_http_method_string_compatibility(self):
        """测试枚举可以作为字符串使用"""
        # 枚举值本身等于字符串
        self.assertEqual(HttpMethod.GET, "GET")
        # 可以直接比较
        method = HttpMethod.GET
        self.assertEqual(method, "GET")


class TestSchemaType(unittest.TestCase):
    """SchemaType 枚举测试"""
    
    def test_schema_type_values(self):
        """测试 Schema 类型枚举值"""
        self.assertEqual(SchemaType.STRING, "string")
        self.assertEqual(SchemaType.INTEGER, "integer")
        self.assertEqual(SchemaType.NUMBER, "number")
        self.assertEqual(SchemaType.BOOLEAN, "boolean")
        self.assertEqual(SchemaType.ARRAY, "array")
        self.assertEqual(SchemaType.OBJECT, "object")


class TestFormat(unittest.TestCase):
    """Format 枚举测试"""
    
    def test_format_values(self):
        """测试格式枚举值"""
        self.assertEqual(Format.EMAIL, "email")
        self.assertEqual(Format.DATE_TIME, "date-time")
        self.assertEqual(Format.URI, "uri")
        self.assertEqual(Format.UUID, "uuid")
        self.assertEqual(Format.BEARER, "bearer")
        self.assertEqual(Format.INT32, "int32")
        self.assertEqual(Format.INT64, "int64")


class TestContentType(unittest.TestCase):
    """ContentType 枚举测试"""
    
    def test_content_type_values(self):
        """测试内容类型枚举值"""
        self.assertEqual(ContentType.JSON, "application/json")
        self.assertEqual(ContentType.XML, "application/xml")
        self.assertEqual(ContentType.FORM_URLENCODED, "application/x-www-form-urlencoded")
        self.assertEqual(ContentType.FORM_DATA, "multipart/form-data")
        self.assertEqual(ContentType.TEXT_PLAIN, "text/plain")


if __name__ == "__main__":
    unittest.main()

