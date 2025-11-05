"""枚举类定义"""

from enum import Enum


class ParamIn(str, Enum):
    """参数位置枚举"""
    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    COOKIE = "cookie"


class HttpMethod(str, Enum):
    """HTTP 方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"


class SchemaType(str, Enum):
    """Schema 类型枚举"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class Format(str, Enum):
    """格式枚举（OpenAPI 常用格式）"""
    # 字符串格式
    EMAIL = "email"
    DATE = "date"
    DATE_TIME = "date-time"
    TIME = "time"
    URI = "uri"
    URL = "url"
    UUID = "uuid"
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    HOSTNAME = "hostname"
    # 数字格式
    INT32 = "int32"
    INT64 = "int64"
    FLOAT = "float"
    DOUBLE = "double"
    # 其他格式
    BYTE = "byte"
    BINARY = "binary"
    PASSWORD = "password"
    BEARER = "bearer"


class ContentType(str, Enum):
    """内容类型枚举"""
    JSON = "application/json"
    XML = "application/xml"
    FORM_URLENCODED = "application/x-www-form-urlencoded"
    FORM_DATA = "multipart/form-data"
    TEXT_PLAIN = "text/plain"
    TEXT_HTML = "text/html"
    OCTET_STREAM = "application/octet-stream"


class SecuritySchemeType(str, Enum):
    """安全方案类型枚举"""
    API_KEY = "apiKey"
    HTTP = "http"
    OAUTH2 = "oauth2"
    OPENID_CONNECT = "openIdConnect"


class ApiKeyLocation(str, Enum):
    """API Key 位置枚举"""
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"

