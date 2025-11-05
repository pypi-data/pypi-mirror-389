"""JSON 生成器"""

import json
from typing import Dict, Any, Optional
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.enums import SchemaType, Format, ContentType


class JSONGenerator:
    """JSON 生成器类"""
    
    @staticmethod
    def _convert_schema_to_dict(schema) -> Dict[str, Any]:
        """将 Schema 对象转换为字典"""
        if schema is None:
            return {}
        
        # 如果 schema 有 ref 引用，直接返回 $ref
        if hasattr(schema, 'ref') and schema.ref:
            return {"$ref": schema.ref}
        
        result = {
            "type": schema.schema_type.value if isinstance(schema.schema_type, SchemaType) else schema.schema_type
        }
        
        if schema.description:
            result["description"] = schema.description
        
        if schema.example is not None:
            result["example"] = schema.example
        
        if schema.default is not None:
            result["default"] = schema.default
        
        if schema.enum:
            result["enum"] = schema.enum
        
        if schema.format:
            format_value = schema.format.value if isinstance(schema.format, Format) else schema.format
            result["format"] = format_value
        
        if schema.min_value is not None:
            result["minimum"] = schema.min_value
        
        if schema.max_value is not None:
            result["maximum"] = schema.max_value
        
        if schema.min_length is not None:
            result["minLength"] = schema.min_length
        
        if schema.max_length is not None:
            result["maxLength"] = schema.max_length
        
        if schema.pattern:
            result["pattern"] = schema.pattern
        
        if schema.items:
            result["items"] = JSONGenerator._convert_schema_to_dict(schema.items)
        
        if schema.properties:
            result["properties"] = {
                key: JSONGenerator._convert_schema_to_dict(value)
                for key, value in schema.properties.items()
            }
        
        if schema.required:
            result["required"] = schema.required
        
        return result
    
    @staticmethod
    def _convert_parameter_to_dict(param) -> Dict[str, Any]:
        """将 Parameter 对象转换为字典"""
        result = {
            "name": param.name,
            "in": param.param_in.value if hasattr(param.param_in, 'value') else str(param.param_in),
            "required": param.required
        }
        
        if param.description:
            result["description"] = param.description
        
        if param.example is not None:
            result["example"] = param.example
        
        # 构建 schema
        schema = {"type": JSONGenerator._python_type_to_openapi_type(param.param_type)}
        
        if param.format:
            format_value = param.format.value if hasattr(param.format, 'value') else str(param.format)
            schema["format"] = format_value
        
        if param.default is not None:
            schema["default"] = param.default
        
        if param.enum:
            schema["enum"] = param.enum
        
        if param.min_value is not None:
            schema["minimum"] = param.min_value
        
        if param.max_value is not None:
            schema["maximum"] = param.max_value
        
        if param.min_length is not None:
            schema["minLength"] = param.min_length
        
        if param.max_length is not None:
            schema["maxLength"] = param.max_length
        
        if param.pattern:
            schema["pattern"] = param.pattern
        
        result["schema"] = schema
        
        return result
    
    @staticmethod
    def _python_type_to_openapi_type(python_type) -> str:
        """将 Python 类型转换为 OpenAPI 类型"""
        type_mapping = {
            int: "integer",
            float: "number",
            str: "string",
            bool: "boolean",
            list: "array",
            dict: "object"
        }
        return type_mapping.get(python_type, "string")
    
    @staticmethod
    def _convert_response_to_dict(response) -> Dict[str, Any]:
        """将 Response 对象转换为字典"""
        result = {
            "description": response.description
        }
        
        if response.content:
            content_type = response.content.content_type.value if hasattr(response.content.content_type, 'value') else str(response.content.content_type)
            content_dict = {}
            
            # 优先使用 model，如果提供的话
            if response.content.model:
                from swagger_sdk.dataclass_parser import DataclassParser
                from dataclasses import is_dataclass
                if is_dataclass(response.content.model):
                    schema = DataclassParser.parse_dataclass(response.content.model)
                    content_dict["schema"] = JSONGenerator._convert_schema_to_dict(schema)
                else:
                    # 如果不是 dataclass，使用 TypeParser
                    schema_dict = JSONGenerator._convert_type_to_schema_dict(response.content.model)
                    content_dict["schema"] = schema_dict
            elif response.content.schema:
                content_dict["schema"] = JSONGenerator._convert_schema_to_dict(response.content.schema)
            
            result["content"] = {
                content_type: content_dict
            }
        
        if response.headers:
            result["headers"] = {
                key: JSONGenerator._convert_schema_to_dict(value)
                for key, value in response.headers.items()
            }
        
        return result
    
    @staticmethod
    def _convert_type_to_schema_dict(type_hint) -> Dict[str, Any]:
        """将类型注解转换为 schema 字典"""
        from swagger_sdk.type_parser import TypeParser
        return TypeParser.parse_type(type_hint)
    
    @staticmethod
    def _convert_security_scheme_to_dict(scheme) -> Dict[str, Any]:
        """将 SecurityScheme 对象转换为字典"""
        from swagger_sdk.enums import SecuritySchemeType, ApiKeyLocation
        
        result = {
            "type": scheme.scheme_type.value if hasattr(scheme.scheme_type, 'value') else str(scheme.scheme_type)
        }
        
        if scheme.description:
            result["description"] = scheme.description
        
        # API Key 类型
        if scheme.scheme_type == SecuritySchemeType.API_KEY:
            if scheme.name:
                result["name"] = scheme.name
            if scheme.location:
                result["in"] = scheme.location.value if hasattr(scheme.location, 'value') else str(scheme.location)
        
        # HTTP 类型
        elif scheme.scheme_type == SecuritySchemeType.HTTP:
            if scheme.scheme:
                result["scheme"] = scheme.scheme
            if scheme.bearer_format:
                result["bearerFormat"] = scheme.bearer_format
        
        # OAuth2 类型
        elif scheme.scheme_type == SecuritySchemeType.OAUTH2:
            if scheme.flows:
                result["flows"] = scheme.flows
        
        # OpenID Connect 类型
        elif scheme.scheme_type == SecuritySchemeType.OPENID_CONNECT:
            if scheme.open_id_connect_url:
                result["openIdConnectUrl"] = scheme.open_id_connect_url
        
        return result
    
    @staticmethod
    def _convert_security_requirement_to_dict(req) -> Dict[str, Any]:
        """将 SecurityRequirement 对象转换为字典"""
        result = {}
        
        # 如果有关作用域（OAuth2），格式为 {name: [scopes]}
        if req.scopes:
            result[req.name] = req.scopes
        else:
            # 如果没有作用域，格式为 {name: []}
            result[req.name] = []
        
        return result
    
    @staticmethod
    def generate(builder: SwaggerBuilder) -> Dict[str, Any]:
        """生成 OpenAPI 3.0 JSON 文档"""
        # 构建基本信息
        info = {
            "title": builder.title,
            "version": builder.version
        }
        
        if builder.description:
            info["description"] = builder.description
        
        # 构建路径
        paths = {}
        
        for api in builder.apis:
            path = api["path"]
            method = api["method"].value if hasattr(api["method"], 'value') else str(api["method"]).lower()
            
            if path not in paths:
                paths[path] = {}
            
            operation = {}
            
            if api.get("summary"):
                operation["summary"] = api["summary"]
            
            if api.get("description"):
                operation["description"] = api["description"]
            
            if api.get("tags"):
                operation["tags"] = api["tags"]
            
            # 处理安全定义
            if api.get("security"):
                operation["security"] = [
                    JSONGenerator._convert_security_requirement_to_dict(req)
                    for req in api["security"]
                ]
            
            # 处理参数
            if api.get("parameters"):
                operation["parameters"] = [
                    JSONGenerator._convert_parameter_to_dict(param)
                    for param in api["parameters"]
                ]
            
            # 处理请求体
            if api.get("request_body"):
                request_body = api["request_body"]
                request_body_dict = {
                    "required": request_body.required
                }
                
                if request_body.description:
                    request_body_dict["description"] = request_body.description
                
                content_type = request_body.content_type.value if hasattr(request_body.content_type, 'value') else str(request_body.content_type)
                content_dict = {}
                
                # 优先使用 model，如果提供的话
                if request_body.model:
                    from swagger_sdk.dataclass_parser import DataclassParser
                    from dataclasses import is_dataclass
                    if is_dataclass(request_body.model):
                        schema = DataclassParser.parse_dataclass(request_body.model)
                        content_dict["schema"] = JSONGenerator._convert_schema_to_dict(schema)
                    else:
                        # 如果不是 dataclass，使用 TypeParser
                        schema_dict = JSONGenerator._convert_type_to_schema_dict(request_body.model)
                        content_dict["schema"] = schema_dict
                elif request_body.schema:
                    content_dict["schema"] = JSONGenerator._convert_schema_to_dict(request_body.schema)
                
                request_body_dict["content"] = {
                    content_type: content_dict
                }
                
                operation["requestBody"] = request_body_dict
            
            # 处理响应
            if api.get("responses"):
                operation["responses"] = {
                    str(status_code): JSONGenerator._convert_response_to_dict(response)
                    for status_code, response in api["responses"].items()
                }
            
            paths[path][method.lower()] = operation
        
        # 构建 Components 部分
        components = {}
        if builder.components.get("schemas"):
            components["schemas"] = {
                name: JSONGenerator._convert_schema_to_dict(schema)
                for name, schema in builder.components["schemas"].items()
            }
        
        if builder.components.get("securitySchemes"):
            components["securitySchemes"] = {
                name: JSONGenerator._convert_security_scheme_to_dict(scheme)
                for name, scheme in builder.components["securitySchemes"].items()
            }
        
        # 构建完整的 OpenAPI 文档
        openapi_doc = {
            "openapi": "3.0.0",
            "info": info,
            "paths": paths
        }
        
        # 如果有服务器配置，添加到文档中
        if builder.servers:
            openapi_doc["servers"] = builder.servers
        
        # 如果有组件，添加到文档中
        if components:
            openapi_doc["components"] = components
        
        return openapi_doc

