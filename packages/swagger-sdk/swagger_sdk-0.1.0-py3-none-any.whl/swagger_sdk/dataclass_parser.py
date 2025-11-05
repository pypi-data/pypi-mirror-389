"""dataclass 模型解析器"""

import inspect
from dataclasses import fields, is_dataclass
from typing import Any, get_type_hints, get_origin, get_args
from swagger_sdk.models import Schema, Field
from swagger_sdk.enums import SchemaType, Format
from swagger_sdk.type_parser import TypeParser


class DataclassParser:
    """dataclass 模型解析器，用于解析 dataclass 并生成 OpenAPI Schema"""
    
    @staticmethod
    def parse_dataclass(cls: type) -> Schema:
        """
        解析 dataclass 并生成 Schema
        
        Args:
            cls: dataclass 类
        
        Returns:
            Schema 对象
        """
        if not is_dataclass(cls):
            raise ValueError(f"{cls} is not a dataclass")
        
        # 获取所有字段
        dataclass_fields = fields(cls)
        
        # 获取类型注解
        type_hints = get_type_hints(cls)
        
        properties = {}
        required = []
        
        for field_obj in dataclass_fields:
            field_name = field_obj.name
            field_type = type_hints.get(field_name, str)
            
            # 检查是否有默认值
            # dataclass 使用 dataclasses.MISSING 作为默认值的占位符
            from dataclasses import MISSING
            has_default = field_obj.default != MISSING
            has_default_factory = field_obj.default_factory != MISSING
            
            # 判断是否必填
            is_required = not (has_default or has_default_factory)
            
            if is_required:
                required.append(field_name)
            
            # 解析字段类型
            field_schema = DataclassParser._parse_field_type(field_type, field_obj)
            
            properties[field_name] = field_schema
        
        return Schema(
            schema_type=SchemaType.OBJECT,
            properties=properties,
            required=required  # required 可以是空列表，但不能是 None
        )
    
    @staticmethod
    def _parse_field_type(field_type: Any, field_obj: Any) -> Schema:
        """解析字段类型"""
        # 检查字段是否有 Field 元数据
        field_metadata = {}
        if hasattr(field_obj, 'metadata') and field_obj.metadata:
            # dataclass 的 Field 可能有 metadata
            pass
        
        # 检查默认值是否是 Field 对象
        from dataclasses import MISSING
        if isinstance(field_obj.default, Field):
            # 使用 Field 对象中的配置
            field_config = field_obj.default
            field_metadata = {
                "description": field_config.description,
                "default": field_config.default,
                "example": field_config.example,
                "format": field_config.format,
                "min_value": field_config.min_value,
                "max_value": field_config.max_value,
                "pattern": field_config.pattern,
                "min_length": field_config.min_length,
                "max_length": field_config.max_length,
                "enum": field_config.enum,
            }
            # 使用 Field 中的 field_type（如果提供）
            if field_config.field_type:
                field_type = field_config.field_type
        elif field_obj.default != MISSING:
            # 有默认值但不是 Field 对象
            field_metadata["default"] = field_obj.default
        
        # 使用 TypeParser 解析类型
        schema_dict = TypeParser.parse_type(field_type)
        
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
                    # 处理嵌套对象（可能是 dataclass）
                    schema_kwargs["properties"] = {}
                    for prop_key, prop_val in v.items():
                        if isinstance(prop_val, dict):
                            prop_type_str = prop_val.get("type", "string")
                            try:
                                prop_schema_type = SchemaType(prop_type_str)
                            except ValueError:
                                prop_schema_type = SchemaType.STRING
                            schema_kwargs["properties"][prop_key] = Schema(
                                schema_type=prop_schema_type,
                                **{pk: pv for pk, pv in prop_val.items() if pk != "type"}
                            )
                        else:
                            schema_kwargs["properties"][prop_key] = prop_val
                elif k == "additionalProperties" and isinstance(v, dict):
                    # 处理 Dict 类型的 additionalProperties
                    prop_type_str = v.get("type", "string")
                    try:
                        prop_schema_type = SchemaType(prop_type_str)
                    except ValueError:
                        prop_schema_type = SchemaType.STRING
                    schema_kwargs["additionalProperties"] = Schema(
                        schema_type=prop_schema_type,
                        **{pk: pv for pk, pv in v.items() if pk != "type"}
                    )
                else:
                    schema_kwargs[k] = v
        
        # 合并 Field 元数据
        schema_kwargs.update({k: v for k, v in field_metadata.items() if v is not None})
        
        # 检查是否是 dataclass 类型（嵌套对象）
        origin = get_origin(field_type)
        args = get_args(field_type)
        
        # 如果是直接的 dataclass 类型
        if is_dataclass(field_type):
            # 递归解析嵌套的 dataclass
            nested_schema = DataclassParser.parse_dataclass(field_type)
            return nested_schema
        elif origin is not None:
            # 处理泛型类型（如 List[User], Optional[User]）
            # 提取实际类型参数
            for arg in args:
                if is_dataclass(arg):
                    # 如果类型参数是 dataclass，递归解析
                    if schema_type == SchemaType.ARRAY:
                        # 对于数组类型，items 应该是嵌套的 dataclass schema
                        nested_schema = DataclassParser.parse_dataclass(arg)
                        schema_kwargs["items"] = nested_schema
                    elif schema_type == SchemaType.OBJECT:
                        # 对于对象类型，直接使用嵌套的 dataclass schema
                        return DataclassParser.parse_dataclass(arg)
        
        return Schema(schema_type=schema_type, **schema_kwargs)

