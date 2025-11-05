"""Components/Schemas 支持测试"""

import unittest
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.models import Schema
from swagger_sdk.enums import SchemaType


class TestComponents(unittest.TestCase):
    """Components/Schemas 支持测试"""
    
    def test_register_component_schema(self):
        """测试注册 schema 组件"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        user_schema = Schema(
            schema_type=SchemaType.OBJECT,
            properties={
                "id": Schema(schema_type=SchemaType.INTEGER),
                "name": Schema(schema_type=SchemaType.STRING)
            },
            required=["id", "name"]
        )
        
        builder.register_component_schema("User", user_schema)
        
        # 验证组件已注册
        self.assertIn("User", builder.components.get("schemas", {}))
        registered_schema = builder.components["schemas"]["User"]
        self.assertEqual(registered_schema.schema_type, SchemaType.OBJECT)
    
    def test_reuse_component_schema(self):
        """测试重用 schema 组件"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        # 注册组件
        user_schema = Schema(
            schema_type=SchemaType.OBJECT,
            properties={
                "id": Schema(schema_type=SchemaType.INTEGER),
                "name": Schema(schema_type=SchemaType.STRING)
            }
        )
        builder.register_component_schema("User", user_schema)
        
        # 在响应中引用组件（使用 $ref）
        from swagger_sdk.models import Response, ResponseContent
        from swagger_sdk.enums import HttpMethod, ContentType
        
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表",
            responses={
                200: Response(
                    description="成功",
                    content=ResponseContent(
                        content_type=ContentType.JSON,
                        schema=Schema(
                            schema_type=SchemaType.OBJECT,
                            properties={
                                "users": Schema(
                                    schema_type=SchemaType.ARRAY,
                                    items=Schema(
                                        ref="#/components/schemas/User"
                                    )
                                )
                            }
                        )
                    )
                )
            }
        )
        
        # 生成 JSON 并验证 Components 部分
        json_doc = builder.generate_json()
        
        self.assertIn("components", json_doc)
        self.assertIn("schemas", json_doc["components"])
        self.assertIn("User", json_doc["components"]["schemas"])
    
    def test_generate_components_section(self):
        """测试生成 Components 部分"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        # 注册多个组件
        user_schema = Schema(
            schema_type=SchemaType.OBJECT,
            properties={
                "id": Schema(schema_type=SchemaType.INTEGER),
                "name": Schema(schema_type=SchemaType.STRING)
            }
        )
        builder.register_component_schema("User", user_schema)
        
        error_schema = Schema(
            schema_type=SchemaType.OBJECT,
            properties={
                "code": Schema(schema_type=SchemaType.INTEGER),
                "message": Schema(schema_type=SchemaType.STRING)
            }
        )
        builder.register_component_schema("Error", error_schema)
        
        json_doc = builder.generate_json()
        
        # 验证 Components 部分
        self.assertIn("components", json_doc)
        self.assertIn("schemas", json_doc["components"])
        self.assertEqual(len(json_doc["components"]["schemas"]), 2)
        self.assertIn("User", json_doc["components"]["schemas"])
        self.assertIn("Error", json_doc["components"]["schemas"])

