"""安全定义 YAML 生成测试"""

import unittest
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.models import SecurityScheme, SecurityRequirement
from swagger_sdk.enums import HttpMethod, SecuritySchemeType, ApiKeyLocation


class TestSecurityYAML(unittest.TestCase):
    """安全定义 YAML 生成测试"""
    
    def test_generate_yaml_with_security(self):
        """测试生成包含安全定义的 YAML 文档"""
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
        
        # 生成 YAML
        yaml_doc = builder.generate_yaml()
        
        # 验证 Components 中包含 securitySchemes
        self.assertIn("components:", yaml_doc)
        self.assertIn("securitySchemes:", yaml_doc)
        self.assertIn("apiKey:", yaml_doc)
        
        # 验证接口中包含 security
        self.assertIn("security:", yaml_doc)
        self.assertIn("- apiKey:", yaml_doc)

