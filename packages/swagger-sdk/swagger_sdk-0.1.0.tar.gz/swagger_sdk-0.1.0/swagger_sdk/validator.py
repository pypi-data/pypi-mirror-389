"""文档验证器"""

from typing import List, Tuple
from swagger_sdk.builder import SwaggerBuilder
import re


class Validator:
    """OpenAPI 3.0 文档验证器"""
    
    @staticmethod
    def validate(builder: SwaggerBuilder) -> Tuple[bool, List[str]]:
        """
        验证 OpenAPI 文档
        
        Args:
            builder: SwaggerBuilder 实例
        
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        # 1. 验证基本信息
        if not builder.title:
            errors.append("缺少必需的 'title' 字段")
        
        if not builder.version:
            errors.append("缺少必需的 'version' 字段")
        
        # 2. 验证每个接口
        for api in builder.apis:
            # 验证路径格式
            path = api.get("path", "")
            if not path:
                errors.append(f"接口缺少 'path' 字段")
            elif not path.startswith("/"):
                errors.append(f"路径 '{path}' 必须以 '/' 开头")
            
            # 验证方法
            method = api.get("method")
            if not method:
                errors.append(f"接口 '{path}' 缺少 'method' 字段")
            
            # 验证路径参数
            path_params = Validator._extract_path_params(path)
            defined_params = api.get("parameters", [])
            
            # 检查路径参数是否都有定义
            for path_param in path_params:
                param_found = False
                for param in defined_params:
                    param_name = param.name if hasattr(param, 'name') else param.get('name', '')
                    param_in = param.param_in if hasattr(param, 'param_in') else param.get('in', '')
                    if param_name == path_param and param_in in ['path', 'PATH']:
                        param_found = True
                        break
                
                if not param_found:
                    errors.append(f"路径 '{path}' 中的参数 '{{{path_param}}}' 未在 parameters 中定义")
            
            # 验证响应
            responses = api.get("responses", {})
            if not responses:
                # 响应不是必需的，但建议有
                pass
            
            # 验证组件引用
            Validator._validate_component_references(api, builder, errors, path)
        
        # 3. 验证组件定义
        Validator._validate_components(builder, errors)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _extract_path_params(path: str) -> List[str]:
        """从路径中提取参数名"""
        # 匹配 {param} 格式
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, path)
        return matches
    
    @staticmethod
    def _validate_component_references(api: dict, builder, errors: List[str], path: str):
        """验证组件引用"""
        # 检查响应中的组件引用
        responses = api.get("responses", {})
        for status_code, response in responses.items():
            if hasattr(response, 'content') and response.content:
                if hasattr(response.content, 'schema') and response.content.schema:
                    Validator._validate_schema_ref(
                        response.content.schema, 
                        builder, 
                        errors, 
                        f"{path} -> {status_code} response"
                    )
        
        # 检查请求体中的组件引用
        request_body = api.get("request_body")
        if request_body and hasattr(request_body, 'schema') and request_body.schema:
            Validator._validate_schema_ref(
                request_body.schema,
                builder,
                errors,
                f"{path} -> request body"
            )
        
        # 检查参数中的组件引用
        parameters = api.get("parameters", [])
        for param in parameters:
            if hasattr(param, 'schema') and param.schema:
                Validator._validate_schema_ref(
                    param.schema,
                    builder,
                    errors,
                    f"{path} -> parameter {getattr(param, 'name', 'unknown')}"
                )
    
    @staticmethod
    def _validate_schema_ref(schema, builder, errors: List[str], context: str):
        """递归验证 schema 中的组件引用"""
        if hasattr(schema, 'ref') and schema.ref:
            # 检查引用是否有效
            ref_path = schema.ref
            if ref_path.startswith("#/components/schemas/"):
                component_name = ref_path.replace("#/components/schemas/", "")
                if component_name not in builder.components.get("schemas", {}):
                    errors.append(f"{context}: 引用的组件 '{component_name}' 不存在")
        
        # 递归检查 items
        if hasattr(schema, 'items') and schema.items:
            Validator._validate_schema_ref(schema.items, builder, errors, context)
        
        # 递归检查 properties
        if hasattr(schema, 'properties') and schema.properties:
            for prop_name, prop_schema in schema.properties.items():
                Validator._validate_schema_ref(prop_schema, builder, errors, f"{context} -> {prop_name}")
        
        # 递归检查 additionalProperties
        if hasattr(schema, 'additionalProperties') and schema.additionalProperties:
            if isinstance(schema.additionalProperties, dict):
                # 如果是字典，可能是 Schema 对象
                pass
            elif hasattr(schema.additionalProperties, 'ref'):
                Validator._validate_schema_ref(schema.additionalProperties, builder, errors, context)
    
    @staticmethod
    def _validate_components(builder, errors: List[str]):
        """验证组件定义"""
        schemas = builder.components.get("schemas", {})
        for name, schema in schemas.items():
            # 验证组件名称格式
            if not name or not isinstance(name, str):
                errors.append(f"组件名称 '{name}' 无效")
            
            # 验证 schema 对象
            if schema is None:
                errors.append(f"组件 '{name}' 的 schema 为空")

