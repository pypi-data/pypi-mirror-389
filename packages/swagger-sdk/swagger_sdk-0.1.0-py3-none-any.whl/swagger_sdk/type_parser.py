"""类型注解解析器"""

import typing
from typing import get_origin, get_args, Union, Optional, List, Dict, Any
from swagger_sdk.enums import SchemaType


class TypeParser:
    """类型注解解析器，用于将 Python 类型注解转换为 OpenAPI Schema"""
    
    @staticmethod
    def parse_type(type_hint: Any) -> dict:
        """
        解析类型注解，返回 OpenAPI Schema 字典
        
        Args:
            type_hint: Python 类型注解
        
        Returns:
            OpenAPI Schema 字典
        """
        # 处理 None 类型
        if type_hint is None:
            return {"type": "object"}
        
        # 处理基本类型
        type_mapping = {
            int: "integer",
            float: "number",
            str: "string",
            bool: "boolean",
            dict: "object",
            list: "array",
            tuple: "array",
            object: "string",  # 未知类型默认返回 string
        }
        
        if type_hint in type_mapping:
            return {"type": type_mapping[type_hint]}
        
        # 处理 Optional 类型（Union[Something, None]）
        origin = get_origin(type_hint)
        args = get_args(type_hint)
        
        if origin is Union:
            # Optional 是 Union[T, None] 的别名
            # 提取非 None 的类型
            non_none_types = [arg for arg in args if arg is not type(None)]
            if len(non_none_types) == 1:
                return TypeParser.parse_type(non_none_types[0])
            # 如果有多个非 None 类型，返回第一个
            if non_none_types:
                return TypeParser.parse_type(non_none_types[0])
        
        # 处理 List 类型
        if origin is list or (hasattr(typing, 'List') and origin is typing.List):
            result = {"type": "array"}
            if args:
                result["items"] = TypeParser.parse_type(args[0])
            else:
                result["items"] = {"type": "string"}  # 默认类型
            return result
        
        # 处理 Dict 类型
        if origin is dict or (hasattr(typing, 'Dict') and origin is typing.Dict):
            result = {"type": "object"}
            if args and len(args) >= 2:
                # Dict[key_type, value_type]
                # OpenAPI 中 object 的 additionalProperties 表示值的类型
                result["additionalProperties"] = TypeParser.parse_type(args[1])
            else:
                result["additionalProperties"] = {"type": "string"}
            return result
        
        # 处理 Tuple 类型（作为数组处理）
        if origin is tuple or (hasattr(typing, 'Tuple') and origin is typing.Tuple):
            result = {"type": "array"}
            if args:
                result["items"] = TypeParser.parse_type(args[0])
            else:
                result["items"] = {"type": "string"}
            return result
        
        # 处理其他类型（如自定义类）
        # 尝试获取类型名称
        if hasattr(type_hint, '__name__'):
            type_name = type_hint.__name__
            # 如果是常见类型，尝试映射
            if type_name == 'datetime':
                return {"type": "string", "format": "date-time"}
            elif type_name == 'date':
                return {"type": "string", "format": "date"}
            elif type_name == 'time':
                return {"type": "string", "format": "time"}
            elif type_name == 'UUID':
                return {"type": "string", "format": "uuid"}
        
        # 默认返回 object 类型
        return {"type": "object"}

