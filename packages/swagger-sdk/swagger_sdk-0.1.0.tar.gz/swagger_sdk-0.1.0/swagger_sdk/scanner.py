"""扫描器实现"""

import inspect
from typing import Any, List, Dict, get_type_hints
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.type_parser import TypeParser
from swagger_sdk.docstring_parser import DocstringParser
from swagger_sdk.models import Parameter, Response, ResponseContent, Schema
from swagger_sdk.enums import ParamIn, ContentType, SchemaType


class Scanner:
    """扫描器类，用于扫描模块中的装饰器接口"""
    
    @staticmethod
    def _extract_parameters_from_signature(func) -> List[Parameter]:
        """从函数签名提取参数"""
        sig = inspect.signature(func)
        params = []
        docstring_info = DocstringParser.parse(func.__doc__)
        
        # 获取 API 路径（用于判断路径参数）
        api_path = ""
        if hasattr(func, '_swagger_api'):
            api_path = func._swagger_api.get('path', '')
        
        for param_name, param in sig.parameters.items():
            # 跳过 self 参数
            if param_name == 'self':
                continue
            
            # 确定参数位置
            # 如果参数名在路径中（如 {user_id}），则是路径参数
            param_in = ParamIn.PATH if f"{{{param_name}}}" in api_path or f"<{param_name}>" in api_path else ParamIn.QUERY
            
            # 获取参数类型
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
            
            # 获取参数描述（从docstring）
            description = None
            if "Args" in docstring_info and param_name in docstring_info["Args"]:
                description = docstring_info["Args"][param_name]
            
            # 判断是否必填
            # 路径参数总是必填的，query参数如果有默认值则不必填
            required = param_in == ParamIn.PATH or param.default == inspect.Parameter.empty
            
            # 创建 Parameter 对象
            param_obj = Parameter(
                name=param_name,
                param_type=param_type,
                param_in=param_in,
                required=required,
                description=description,
                default=param.default if param.default != inspect.Parameter.empty else None
            )
            params.append(param_obj)
        
        return params
    
    @staticmethod
    def _extract_response_from_signature(func) -> Dict[int, Response]:
        """从函数签名提取响应信息"""
        sig = inspect.signature(func)
        return_annotation = sig.return_annotation
        
        if return_annotation == inspect.Signature.empty or return_annotation is None:
            return {}
        
        # 解析返回类型
        schema_dict = TypeParser.parse_type(return_annotation)
        
        # 转换 schema_type 字符串为 SchemaType 枚举
        schema_type_str = schema_dict.get("type", "object")
        try:
            schema_type = SchemaType(schema_type_str)
        except ValueError:
            schema_type = SchemaType.OBJECT
        
        # 构建 Schema 对象
        schema_kwargs = {}
        for k, v in schema_dict.items():
            if k != "type":
                if k == "items" and isinstance(v, dict):
                    # 递归处理 items
                    item_type_str = v.get("type", "string")
                    try:
                        item_schema_type = SchemaType(item_type_str)
                    except ValueError:
                        item_schema_type = SchemaType.STRING
                    schema_kwargs["items"] = Schema(
                        schema_type=item_schema_type,
                        **{ik: iv for ik, iv in v.items() if ik != "type"}
                    )
                elif k == "properties" and isinstance(v, dict):
                    # 处理嵌套 properties
                    schema_kwargs["properties"] = {
                        prop_key: Schema(
                            schema_type=SchemaType(prop_val.get("type", "string")),
                            **{pk: pv for pk, pv in prop_val.items() if pk != "type"}
                        ) for prop_key, prop_val in v.items()
                    }
                else:
                    schema_kwargs[k] = v
        
        schema = Schema(schema_type=schema_type, **schema_kwargs)
        
        # 获取返回描述（从docstring）
        docstring_info = DocstringParser.parse(func.__doc__)
        description = docstring_info.get("Returns", "成功")
        
        response = Response(
            description=description,
            content=ResponseContent(
                content_type=ContentType.JSON,
                schema=schema
            )
        )
        
        return {200: response}
    
    @staticmethod
    def scan_module(builder: SwaggerBuilder, module: Any):
        """
        扫描模块中的装饰器接口
        
        Args:
            builder: SwaggerBuilder 实例
            module: 要扫描的模块
        """
        # 扫描模块级别的函数
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if hasattr(obj, '_swagger_api'):
                api_info = obj._swagger_api.copy()
                api_info['handler'] = obj
                
                # 自动提取参数（如果装饰器没有指定参数）
                if not api_info.get('parameters'):
                    try:
                        api_info['parameters'] = Scanner._extract_parameters_from_signature(obj)
                    except Exception:
                        pass  # 如果提取失败，保持为空
                
                # 自动提取响应（如果装饰器没有指定响应）
                if not api_info.get('responses'):
                    try:
                        api_info['responses'] = Scanner._extract_response_from_signature(obj)
                    except Exception:
                        pass  # 如果提取失败，保持为空
                
                # 自动提取描述（如果装饰器没有指定描述）
                if not api_info.get('description'):
                    docstring_info = DocstringParser.parse(obj.__doc__)
                    if docstring_info.get('summary'):
                        api_info['description'] = docstring_info['summary']
                
                builder.apis.append(api_info)
        
        # 扫描类
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # 检查是否有控制器装饰器
            controller_info = None
            if hasattr(obj, '_swagger_controller'):
                controller_info = obj._swagger_controller
            
            # 扫描类中的方法
            for method_name, method in inspect.getmembers(obj, inspect.ismethod):
                if hasattr(method, '_swagger_api'):
                    api_info = method._swagger_api.copy()
                    api_info['handler'] = method
                    
                    # 自动提取参数、响应和描述
                    Scanner._enhance_api_info(api_info, method)
                    
                    # 如果有控制器信息，合并路径和标签
                    if controller_info:
                        prefix = controller_info.get('prefix', '')
                        # 合并路径
                        if api_info['path'].startswith('/'):
                            api_info['path'] = prefix + api_info['path']
                        else:
                            api_info['path'] = prefix + '/' + api_info['path']
                        
                        # 合并标签
                        controller_tags = controller_info.get('tags', [])
                        api_tags = api_info.get('tags', [])
                        api_info['tags'] = list(set(controller_tags + api_tags))
                        
                        # 添加控制器描述
                        if controller_info.get('description'):
                            if api_info.get('description'):
                                api_info['description'] = controller_info['description'] + '\n' + api_info['description']
                            else:
                                api_info['description'] = controller_info['description']
                    
                    builder.apis.append(api_info)
            
            # 也检查未绑定方法（类方法）
            for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                if hasattr(method, '_swagger_api'):
                    api_info = method._swagger_api.copy()
                    api_info['handler'] = method
                    
                    # 自动提取参数、响应和描述
                    Scanner._enhance_api_info(api_info, method)
                    
                    # 如果有控制器信息，合并路径和标签
                    if controller_info:
                        prefix = controller_info.get('prefix', '')
                        # 合并路径
                        if api_info['path'].startswith('/'):
                            api_info['path'] = prefix + api_info['path']
                        else:
                            api_info['path'] = prefix + '/' + api_info['path']
                        
                        # 合并标签
                        controller_tags = controller_info.get('tags', [])
                        api_tags = api_info.get('tags', [])
                        api_info['tags'] = list(set(controller_tags + api_tags))
                        
                        # 添加控制器描述
                        if controller_info.get('description'):
                            if api_info.get('description'):
                                api_info['description'] = controller_info['description'] + '\n' + api_info['description']
                            else:
                                api_info['description'] = controller_info['description']
                    
                    builder.apis.append(api_info)
    
    @staticmethod
    def _enhance_api_info(api_info: Dict, func: Any):
        """增强 API 信息：自动提取参数、响应和描述"""
        # 自动提取参数（如果装饰器没有指定参数）
        if not api_info.get('parameters'):
            try:
                api_info['parameters'] = Scanner._extract_parameters_from_signature(func)
            except Exception:
                pass
        
        # 自动提取响应（如果装饰器没有指定响应）
        if not api_info.get('responses'):
            try:
                api_info['responses'] = Scanner._extract_response_from_signature(func)
            except Exception:
                pass
        
        # 自动提取描述（如果装饰器没有指定描述）
        if not api_info.get('description'):
            docstring_info = DocstringParser.parse(func.__doc__)
            if docstring_info.get('summary'):
                api_info['description'] = docstring_info['summary']

