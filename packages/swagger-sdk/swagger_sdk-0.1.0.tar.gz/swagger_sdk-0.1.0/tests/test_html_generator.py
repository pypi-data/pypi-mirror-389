"""HTML 生成功能测试"""

import unittest
import os
import tempfile
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.enums import HttpMethod


class TestHTMLGenerator(unittest.TestCase):
    """HTML 生成功能测试"""
    
    def test_generate_basic_html(self):
        """测试生成基本的 HTML 文档"""
        builder = SwaggerBuilder(
            title="Test API",
            version="1.0.0",
            description="测试API"
        )
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表"
        )
        
        html = builder.generate_html()
        
        # 验证基本 HTML 结构
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<html", html)
        self.assertIn("</html>", html)
        self.assertIn("Test API", html)
        self.assertIn("1.0.0", html)
    
    def test_generate_html_with_swagger_ui(self):
        """测试生成包含 Swagger UI 的 HTML"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表"
        )
        
        html = builder.generate_html()
        
        # 验证包含 Swagger UI 相关的内容
        # 应该包含 Swagger UI 的 script 标签或初始化代码
        self.assertIn("swagger", html.lower())
        # 或者包含 OpenAPI 文档的引用
        self.assertIn("openapi", html.lower())
    
    def test_generate_html_save_to_file(self):
        """测试保存 HTML 到文件"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(path="/api/users", method=HttpMethod.GET, summary="获取用户")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8') as f:
            temp_path = f.name
        
        try:
            html = builder.generate_html(output_path=temp_path)
            
            # 验证文件存在
            self.assertTrue(os.path.exists(temp_path))
            
            # 验证文件内容
            with open(temp_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            self.assertIn("Test API", file_content)
            self.assertIn("<!DOCTYPE html>", file_content)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_generate_html_with_api_documentation(self):
        """测试生成包含 API 文档的 HTML"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(
            path="/api/users/{user_id}",
            method=HttpMethod.GET,
            summary="获取用户详情",
            description="根据用户ID获取用户详细信息"
        )
        
        html = builder.generate_html()
        
        # 验证包含 API 信息
        self.assertIn("获取用户详情", html)
        self.assertIn("/api/users/{user_id}", html)

