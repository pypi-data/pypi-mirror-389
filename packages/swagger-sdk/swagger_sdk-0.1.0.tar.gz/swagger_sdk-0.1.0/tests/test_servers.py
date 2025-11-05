"""Servers 配置测试"""

import unittest
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.enums import HttpMethod


class TestServers(unittest.TestCase):
    """Servers 配置测试"""
    
    def test_init_with_servers(self):
        """测试初始化时设置 servers"""
        servers = [
            {"url": "https://api.example.com", "description": "生产环境"},
            {"url": "https://staging.example.com", "description": "测试环境"}
        ]
        builder = SwaggerBuilder(
            title="Test API",
            version="1.0.0",
            servers=servers
        )
        self.assertEqual(len(builder.servers), 2)
        self.assertEqual(builder.servers[0]["url"], "https://api.example.com")
        self.assertEqual(builder.servers[1]["url"], "https://staging.example.com")
    
    def test_add_server(self):
        """测试添加服务器"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.add_server("https://api.example.com", description="生产环境")
        self.assertEqual(len(builder.servers), 1)
        self.assertEqual(builder.servers[0]["url"], "https://api.example.com")
        self.assertEqual(builder.servers[0]["description"], "生产环境")
    
    def test_add_server_with_variables(self):
        """测试添加带变量的服务器"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        variables = {
            "protocol": {
                "default": "https",
                "enum": ["http", "https"]
            },
            "port": {
                "default": "443",
                "enum": ["80", "443"]
            }
        }
        builder.add_server(
            "https://api.example.com:{port}",
            description="带变量的服务器",
            variables=variables
        )
        self.assertEqual(len(builder.servers), 1)
        self.assertIn("variables", builder.servers[0])
        self.assertEqual(builder.servers[0]["variables"], variables)
    
    def test_set_servers(self):
        """测试设置服务器列表"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.add_server("https://api.example.com")
        
        new_servers = [
            {"url": "https://api1.example.com"},
            {"url": "https://api2.example.com"}
        ]
        builder.set_servers(new_servers)
        self.assertEqual(len(builder.servers), 2)
        self.assertEqual(builder.servers[0]["url"], "https://api1.example.com")
    
    def test_servers_in_json_output(self):
        """测试 servers 在 JSON 输出中"""
        builder = SwaggerBuilder(
            title="Test API",
            version="1.0.0",
            servers=[
                {"url": "https://api.example.com", "description": "生产环境"}
            ]
        )
        builder.register_api(
            path="/test",
            method=HttpMethod.GET,
            summary="测试接口"
        )
        
        json_doc = builder.generate_json()
        self.assertIn("servers", json_doc)
        self.assertEqual(len(json_doc["servers"]), 1)
        self.assertEqual(json_doc["servers"][0]["url"], "https://api.example.com")
        self.assertEqual(json_doc["servers"][0]["description"], "生产环境")
    
    def test_servers_not_in_json_when_empty(self):
        """测试当 servers 为空时不在 JSON 中"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        builder.register_api(
            path="/test",
            method=HttpMethod.GET,
            summary="测试接口"
        )
        
        json_doc = builder.generate_json()
        self.assertNotIn("servers", json_doc)
    
    def test_multiple_servers_in_json(self):
        """测试多个服务器在 JSON 中"""
        builder = SwaggerBuilder(
            title="Test API",
            version="1.0.0"
        )
        builder.add_server("https://api.example.com", "生产环境")
        builder.add_server("https://staging.example.com", "测试环境")
        builder.add_server("https://dev.example.com", "开发环境")
        
        json_doc = builder.generate_json()
        self.assertIn("servers", json_doc)
        self.assertEqual(len(json_doc["servers"]), 3)

