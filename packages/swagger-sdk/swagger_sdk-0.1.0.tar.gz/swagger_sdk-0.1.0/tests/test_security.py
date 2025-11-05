"""安全定义（Security）支持测试"""

import unittest
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.enums import HttpMethod
from swagger_sdk.models import SecurityScheme, SecurityRequirement
from swagger_sdk.enums import SecuritySchemeType, ApiKeyLocation


class TestSecurity(unittest.TestCase):
    """安全定义支持测试"""
    
    def test_register_security_scheme_api_key(self):
        """测试注册 API Key 安全方案"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        # 注册 API Key 安全方案
        scheme = SecurityScheme(
            scheme_type=SecuritySchemeType.API_KEY,
            name="X-API-Key",
            location=ApiKeyLocation.HEADER,
            description="API Key 认证"
        )
        
        builder.register_security_scheme("apiKey", scheme)
        
        # 验证安全方案已注册
        self.assertIn("apiKey", builder.components.get("securitySchemes", {}))
        registered_scheme = builder.components["securitySchemes"]["apiKey"]
        self.assertEqual(registered_scheme.scheme_type, SecuritySchemeType.API_KEY)
        self.assertEqual(registered_scheme.name, "X-API-Key")
    
    def test_register_security_scheme_http_bearer(self):
        """测试注册 HTTP Bearer 安全方案"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        scheme = SecurityScheme(
            scheme_type=SecuritySchemeType.HTTP,
            scheme="bearer",
            bearer_format="JWT",
            description="Bearer Token 认证"
        )
        
        builder.register_security_scheme("bearerAuth", scheme)
        
        # 验证安全方案已注册
        self.assertIn("bearerAuth", builder.components["securitySchemes"])
        registered_scheme = builder.components["securitySchemes"]["bearerAuth"]
        self.assertEqual(registered_scheme.scheme_type, SecuritySchemeType.HTTP)
        self.assertEqual(registered_scheme.scheme, "bearer")
    
    def test_register_security_scheme_http_basic(self):
        """测试注册 HTTP Basic 安全方案"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        scheme = SecurityScheme(
            scheme_type=SecuritySchemeType.HTTP,
            scheme="basic",
            description="HTTP Basic 认证"
        )
        
        builder.register_security_scheme("basicAuth", scheme)
        
        registered_scheme = builder.components["securitySchemes"]["basicAuth"]
        self.assertEqual(registered_scheme.scheme, "basic")
    
    def test_apply_security_to_api(self):
        """测试在接口中应用安全定义"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        # 注册安全方案
        scheme = SecurityScheme(
            scheme_type=SecuritySchemeType.API_KEY,
            name="X-API-Key",
            location=ApiKeyLocation.HEADER
        )
        builder.register_security_scheme("apiKey", scheme)
        
        # 注册接口并应用安全定义
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表",
            security=[SecurityRequirement(name="apiKey")]
        )
        
        # 验证安全定义已应用
        api = builder.apis[0]
        self.assertIn("security", api)
        self.assertEqual(len(api["security"]), 1)
        self.assertEqual(api["security"][0].name, "apiKey")
    
    def test_apply_multiple_security_to_api(self):
        """测试在接口中应用多个安全定义（OR关系）"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        # 注册多个安全方案
        api_key_scheme = SecurityScheme(
            scheme_type=SecuritySchemeType.API_KEY,
            name="X-API-Key",
            location=ApiKeyLocation.HEADER
        )
        bearer_scheme = SecurityScheme(
            scheme_type=SecuritySchemeType.HTTP,
            scheme="bearer"
        )
        
        builder.register_security_scheme("apiKey", api_key_scheme)
        builder.register_security_scheme("bearerAuth", bearer_scheme)
        
        # 应用多个安全定义（OR关系 - 满足任一即可）
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表",
            security=[
                SecurityRequirement(name="apiKey"),
                SecurityRequirement(name="bearerAuth")
            ]
        )
        
        api = builder.apis[0]
        self.assertEqual(len(api["security"]), 2)
    
    def test_apply_security_with_scopes(self):
        """测试应用带作用域的安全定义（OAuth2）"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        # 注册 OAuth2 安全方案
        oauth2_scheme = SecurityScheme(
            scheme_type=SecuritySchemeType.OAUTH2,
            flows={
                "authorizationCode": {
                    "authorizationUrl": "https://example.com/oauth/authorize",
                    "tokenUrl": "https://example.com/oauth/token",
                    "scopes": {
                        "read": "读取权限",
                        "write": "写入权限"
                    }
                }
            }
        )
        builder.register_security_scheme("oauth2", oauth2_scheme)
        
        # 应用带作用域的安全定义
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表",
            security=[SecurityRequirement(name="oauth2", scopes=["read"])]
        )
        
        api = builder.apis[0]
        security_req = api["security"][0]
        self.assertEqual(security_req.name, "oauth2")
        self.assertEqual(security_req.scopes, ["read"])
    
    def test_generate_json_with_security(self):
        """测试生成包含安全定义的 JSON 文档"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        # 注册安全方案
        scheme = SecurityScheme(
            scheme_type=SecuritySchemeType.API_KEY,
            name="X-API-Key",
            location=ApiKeyLocation.HEADER
        )
        builder.register_security_scheme("apiKey", scheme)
        
        # 注册接口并应用安全定义
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表",
            security=[SecurityRequirement(name="apiKey")]
        )
        
        # 生成 JSON
        json_doc = builder.generate_json()
        
        # 验证 Components 中包含 securitySchemes
        self.assertIn("components", json_doc)
        self.assertIn("securitySchemes", json_doc["components"])
        self.assertIn("apiKey", json_doc["components"]["securitySchemes"])
        
        # 验证接口中包含 security
        operation = json_doc["paths"]["/api/users"]["get"]
        self.assertIn("security", operation)
        self.assertEqual(len(operation["security"]), 1)
        self.assertIn("apiKey", operation["security"][0])

