"""基础模型类定义"""

from typing import Optional, Any, List, Dict, Type
from swagger_sdk.enums import ParamIn, Format, SchemaType, ContentType, SecuritySchemeType, ApiKeyLocation

class Parameter:
    """参数配置类"""
    
    def __init__(
        self,
        name: str,
        param_type: Type,
        param_in: ParamIn = ParamIn.QUERY,
        required: bool = True,
        description: Optional[str] = None,
        default: Any = None,
        example: Any = None,
        enum: Optional[List] = None,
        format: Optional[Format] = None,
        min_value: Any = None,
        max_value: Any = None,
        pattern: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        **kwargs
    ):
        self.name = name
        self.param_type = param_type
        self.param_in = param_in
        self.required = required
        self.description = description
        self.default = default
        self.example = example
        self.enum = enum
        self.format = format
        self.min_value = min_value
        self.max_value = max_value
        self.pattern = pattern
        self.min_length = min_length
        self.max_length = max_length
        # 存储其他额外参数
        for key, value in kwargs.items():
            setattr(self, key, value)


class Field:
    """字段配置类"""
    
    def __init__(
        self,
        field_type: Optional[Type] = None,
        required: bool = True,
        description: Optional[str] = None,
        default: Any = None,
        example: Any = None,
        enum: Optional[List] = None,
        format: Optional[Format] = None,
        min_value: Any = None,
        max_value: Any = None,
        pattern: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        **kwargs
    ):
        self.field_type = field_type
        self.required = required
        self.description = description
        self.default = default
        self.example = example
        self.enum = enum
        self.format = format
        self.min_value = min_value
        self.max_value = max_value
        self.pattern = pattern
        self.min_length = min_length
        self.max_length = max_length
        # 存储其他额外参数
        for key, value in kwargs.items():
            setattr(self, key, value)


class Schema:
    """Schema 定义类（用于定义字段的 schema）"""
    
    def __init__(
        self,
        schema_type: SchemaType = None,
        description: Optional[str] = None,
        default: Any = None,
        example: Any = None,
        enum: Optional[List] = None,
        format: Optional[Format] = None,
        min_value: Any = None,
        max_value: Any = None,
        pattern: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        items: Optional['Schema'] = None,
        properties: Optional[Dict[str, 'Schema']] = None,
        required: Optional[List[str]] = None,
        ref: Optional[str] = None,  # 支持 $ref 引用
        **kwargs
    ):
        # 如果提供了 ref，schema_type 不是必需的
        self.ref = ref
        self.schema_type = schema_type
        self.description = description
        self.default = default
        self.example = example
        self.enum = enum
        self.format = format
        self.min_value = min_value
        self.max_value = max_value
        self.pattern = pattern
        self.min_length = min_length
        self.max_length = max_length
        self.items = items
        self.properties = properties
        self.required = required
        # 存储其他额外参数
        for key, value in kwargs.items():
            if key != 'ref':  # ref 已经单独处理
                setattr(self, key, value)


class RequestBody:
    """请求体定义类"""
    
    def __init__(
        self,
        required: bool = True,
        description: Optional[str] = None,
        content_type: ContentType = ContentType.JSON,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        **kwargs
    ):
        self.required = required
        self.description = description
        self.content_type = content_type
        self.schema = schema
        self.model = model
        # 存储其他额外参数
        for key, value in kwargs.items():
            setattr(self, key, value)


class ResponseContent:
    """响应内容定义类"""
    
    def __init__(
        self,
        content_type: ContentType = ContentType.JSON,
        schema: Optional[Schema] = None,
        model: Optional[Type] = None,
        **kwargs
    ):
        self.content_type = content_type
        self.schema = schema
        self.model = model
        # 存储其他额外参数
        for key, value in kwargs.items():
            setattr(self, key, value)


class Response:
    """响应定义类"""
    
    def __init__(
        self,
        description: str,
        content: Optional[ResponseContent] = None,
        headers: Optional[Dict[str, Schema]] = None,
        **kwargs
    ):
        self.description = description
        self.content = content
        self.headers = headers
        # 存储其他额外参数
        for key, value in kwargs.items():
            setattr(self, key, value)


class SecurityScheme:
    """安全方案定义类"""
    
    def __init__(
        self,
        scheme_type: SecuritySchemeType,
        description: Optional[str] = None,
        name: Optional[str] = None,  # API Key 名称
        location: Optional[ApiKeyLocation] = None,  # API Key 位置
        scheme: Optional[str] = None,  # HTTP 认证方案（如 "bearer", "basic"）
        bearer_format: Optional[str] = None,  # Bearer Token 格式（如 "JWT"）
        flows: Optional[Dict[str, Any]] = None,  # OAuth2 流程配置
        open_id_connect_url: Optional[str] = None,  # OpenID Connect URL
        **kwargs
    ):
        
        self.scheme_type = scheme_type
        self.description = description
        self.name = name
        self.location = location
        self.scheme = scheme
        self.bearer_format = bearer_format
        self.flows = flows
        self.open_id_connect_url = open_id_connect_url
        # 存储其他额外参数
        for key, value in kwargs.items():
            setattr(self, key, value)


class SecurityRequirement:
    """安全需求定义类（用于在接口中应用安全方案）"""
    
    def __init__(
        self,
        name: str,
        scopes: Optional[List[str]] = None,
        **kwargs
    ):
        """
        初始化安全需求
        
        Args:
            name: 安全方案名称（在 Components 中注册的名称）
            scopes: OAuth2 作用域列表（仅用于 OAuth2 安全方案）
        """
        self.name = name
        self.scopes = scopes or []
        # 存储其他额外参数
        for key, value in kwargs.items():
            setattr(self, key, value)

