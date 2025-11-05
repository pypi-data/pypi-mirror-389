# swagger_sdk - Python Swagger 文档生成 SDK

一个独立、灵活的 Python SDK，用于自动生成符合 OpenAPI 3.0 规范的 Swagger 文档。支持通过装饰器注解和类型注解自动扫描接口，也支持手动注册接口信息。

## 特性

- ✅ **零外部依赖**：仅使用 Python 标准库
- ✅ **自动扫描**：通过装饰器自动发现和解析接口
- ✅ **类型注解解析**：自动从函数签名提取参数和响应类型
- ✅ **多种格式**：支持 JSON、YAML、HTML 格式输出
- ✅ **文档验证**：自动验证生成的文档是否符合 OpenAPI 3.0 规范
- ✅ **文档预览**：本地 HTTP 服务器预览文档
- ✅ **安全定义**：支持 API Key、HTTP、OAuth2、OpenID Connect
- ✅ **组件重用**：支持 Components/Schemas 重用

## 快速开始

### 安装

#### 从 PyPI 安装（推荐）

```bash
pip install swagger-sdk
```

#### 从源码安装

```bash
# 克隆或下载项目
git clone https://github.com/AndsGo/swagger-sdk
cd swagger_sdk

# 安装开发版本
pip install -e .

# 或者直接安装
pip install .
```

### 基本使用

#### 方式一：使用装饰器（推荐）

```python
from swagger_sdk import SwaggerBuilder, swagger_api, HttpMethod
from swagger_sdk.models import Response, ResponseContent
from swagger_sdk.enums import ContentType

# 使用装饰器定义接口
@swagger_api(
    path="/api/users",
    method=HttpMethod.GET,
    summary="获取用户列表"
)
def get_users(page: int = 1, size: int = 10):
    """获取用户列表
    
    Args:
        page: 页码，从1开始
        size: 每页数量，默认10
    
    Returns:
        用户列表和总数
    """
    return {"users": [], "total": 0}

# 创建构建器并扫描
builder = SwaggerBuilder(title="My API", version="1.0.0")
builder.scan(__import__(__name__))

# 生成文档
json_doc = builder.generate_json()
yaml_doc = builder.generate_yaml()
html_doc = builder.generate_html()

# 保存到文件
builder.generate_json(output_path="api.json")
builder.generate_yaml(output_path="api.yaml")
builder.generate_html(output_path="api.html")

# 预览文档
builder.preview(port=8080)
```

#### 方式二：手动注册接口

```python
from swagger_sdk import SwaggerBuilder, HttpMethod
from swagger_sdk.models import Parameter, Response, ResponseContent, Schema
from swagger_sdk.enums import ParamIn, SchemaType, ContentType

builder = SwaggerBuilder(title="My API", version="1.0.0")

# 注册接口
builder.register_api(
    path="/api/users/{user_id}",
    method=HttpMethod.GET,
    summary="获取用户详情",
    parameters=[
        Parameter(
            name="user_id",
            param_type=int,
            param_in=ParamIn.PATH,
            required=True,
            description="用户ID",
            example=123
        )
    ],
    responses={
        200: Response(
            description="成功",
            content=ResponseContent(
                content_type=ContentType.JSON,
                schema=Schema(
                    schema_type=SchemaType.OBJECT,
                    properties={
                        "id": Schema(schema_type=SchemaType.INTEGER),
                        "name": Schema(schema_type=SchemaType.STRING)
                    }
                )
            )
        )
    }
)

# 生成文档
json_doc = builder.generate_json()
```

#### 方式三：使用 dataclass 模型

```python
from dataclasses import dataclass
from swagger_sdk import SwaggerBuilder, HttpMethod
from swagger_sdk.models import RequestBody, Response, ResponseContent
from swagger_sdk.enums import ContentType

@dataclass
class UserCreate:
    username: str
    email: str
    age: int = 0

@dataclass
class UserResponse:
    id: int
    username: str
    email: str

builder = SwaggerBuilder(title="My API", version="1.0.0")

builder.register_api(
    path="/api/users",
    method=HttpMethod.POST,
    summary="创建用户",
    request_body=RequestBody(
        required=True,
        model=UserCreate
    ),
    responses={
        200: Response(
            description="成功",
            content=ResponseContent(
                content_type=ContentType.JSON,
                model=UserResponse
            )
        )
    }
)

json_doc = builder.generate_json()
```

## 核心 API

### SwaggerBuilder

主要的构建器类，用于管理接口信息和生成文档。

```python
from swagger_sdk import SwaggerBuilder

builder = SwaggerBuilder(
    title="API 标题",
    version="1.0.0",
    description="API 描述（可选）"
)
```

#### 主要方法

- `register_api()`: 手动注册单个接口
- `register_apis()`: 批量注册接口
- `update_api()`: 更新已注册的接口
- `register_component_schema()`: 注册 schema 组件
- `register_security_scheme()`: 注册安全方案
- `scan()`: 扫描模块中的装饰器接口
- `generate_json()`: 生成 JSON 格式文档
- `generate_yaml()`: 生成 YAML 格式文档
- `generate_html()`: 生成 HTML 格式文档
- `validate()`: 验证文档规范
- `preview()`: 启动预览服务器

### 装饰器

#### @swagger_api

函数级别装饰器，用于标记 API 接口。

```python
from swagger_sdk import swagger_api, HttpMethod
from swagger_sdk.models import Parameter, Response, ResponseContent
from swagger_sdk.enums import ParamIn, ContentType

@swagger_api(
    path="/api/users/{user_id}",
    method=HttpMethod.GET,
    summary="获取用户详情",
    tags=["用户管理"],
    parameters=[
        Parameter(
            name="user_id",
            param_type=int,
            param_in=ParamIn.PATH,
            required=True
        )
    ],
    responses={
        200: Response(
            description="成功",
            content=ResponseContent(content_type=ContentType.JSON)
        )
    }
)
def get_user(user_id: int):
    """获取用户详情"""
    pass
```

#### @swagger_controller

类级别装饰器，用于标记控制器类。

```python
from swagger_sdk import swagger_controller, swagger_api, HttpMethod

@swagger_controller(
    prefix="/api/v1",
    tags=["用户管理"],
    description="用户管理相关接口"
)
class UserController:
    @swagger_api(
        path="/users",
        method=HttpMethod.GET,
        summary="获取用户列表"
    )
    def get_users(self):
        pass
```

## 高级功能

### 安全定义

```python
from swagger_sdk import SwaggerBuilder, HttpMethod
from swagger_sdk.models import SecurityScheme, SecurityRequirement
from swagger_sdk.enums import SecuritySchemeType, ApiKeyLocation

builder = SwaggerBuilder(title="My API", version="1.0.0")

# 注册 API Key 安全方案
api_key_scheme = SecurityScheme(
    scheme_type=SecuritySchemeType.API_KEY,
    name="X-API-Key",
    location=ApiKeyLocation.HEADER,
    description="API Key 认证"
)
builder.register_security_scheme("apiKey", api_key_scheme)

# 注册 Bearer Token 安全方案
bearer_scheme = SecurityScheme(
    scheme_type=SecuritySchemeType.HTTP,
    scheme="bearer",
    bearer_format="JWT",
    description="Bearer Token 认证"
)
builder.register_security_scheme("bearerAuth", bearer_scheme)

# 在接口中应用安全定义
builder.register_api(
    path="/api/users",
    method=HttpMethod.GET,
    summary="获取用户列表",
    security=[SecurityRequirement(name="apiKey")]
)
```

### 组件重用

```python
from swagger_sdk import SwaggerBuilder
from swagger_sdk.models import Schema
from swagger_sdk.enums import SchemaType

builder = SwaggerBuilder(title="My API", version="1.0.0")

# 注册组件
user_schema = Schema(
    schema_type=SchemaType.OBJECT,
    properties={
        "id": Schema(schema_type=SchemaType.INTEGER),
        "name": Schema(schema_type=SchemaType.STRING)
    },
    required=["id", "name"]
)
builder.register_component_schema("User", user_schema)

# 在响应中引用组件
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
                    schema_type=SchemaType.ARRAY,
                    items=Schema(ref="#/components/schemas/User")
                )
            )
        )
    }
)
```

### 批量注册接口

```python
from swagger_sdk import SwaggerBuilder, HttpMethod

builder = SwaggerBuilder(title="My API", version="1.0.0")

apis = [
    {
        "path": "/api/users",
        "method": HttpMethod.GET,
        "summary": "获取用户列表"
    },
    {
        "path": "/api/users/{id}",
        "method": HttpMethod.GET,
        "summary": "获取用户详情"
    }
]

builder.register_apis(apis, tags=["用户管理"])
```

### 配置管理

```python
from swagger_sdk import SwaggerBuilder, ConfigManager
import os

# 方式一：从配置文件加载
config = ConfigManager.load_from_file("config.json")
builder = SwaggerBuilder(**config)

# 方式二：从环境变量加载
os.environ["SWAGGER_TITLE"] = "My API"
os.environ["SWAGGER_VERSION"] = "1.0.0"
config = ConfigManager.load_from_env(prefix="SWAGGER_")
builder = SwaggerBuilder(**config)

# 方式三：合并多个配置源
file_config = ConfigManager.load_from_file("config.json")
env_config = ConfigManager.load_from_env(prefix="SWAGGER_")
merged_config = ConfigManager.merge(file_config, env_config)
builder = SwaggerBuilder(**merged_config)
```

### 日志和调试

```python
from swagger_sdk import SwaggerLogger

# 创建日志器
logger = SwaggerLogger(debug=True)

# 输出日志
logger.info("信息日志")
logger.warning("警告日志")
logger.error("错误日志")
logger.debug("调试日志")
```

## 完整示例

```python
from swagger_sdk import SwaggerBuilder, swagger_api, swagger_controller, HttpMethod
from swagger_sdk.models import Parameter, Response, ResponseContent, SecurityScheme, SecurityRequirement
from swagger_sdk.enums import ParamIn, SchemaType, ContentType, SecuritySchemeType, ApiKeyLocation
from dataclasses import dataclass

# 定义数据模型
@dataclass
class User:
    id: int
    name: str
    email: str

# 定义控制器
@swagger_controller(prefix="/api/v1", tags=["用户管理"])
class UserController:
    @swagger_api(
        path="/users",
        method=HttpMethod.GET,
        summary="获取用户列表"
    )
    def get_users(self, page: int = 1, size: int = 10):
        """获取用户列表"""
        pass

# 创建构建器
builder = SwaggerBuilder(
    title="用户管理 API",
    version="1.0.0",
    description="用户管理相关接口"
)

# 注册安全方案
api_key = SecurityScheme(
    scheme_type=SecuritySchemeType.API_KEY,
    name="X-API-Key",
    location=ApiKeyLocation.HEADER
)
builder.register_security_scheme("apiKey", api_key)

# 扫描装饰器接口
builder.scan(__import__(__name__))

# 手动注册接口
builder.register_api(
    path="/api/v1/users/{user_id}",
    method=HttpMethod.GET,
    summary="获取用户详情",
    parameters=[
        Parameter(
            name="user_id",
            param_type=int,
            param_in=ParamIn.PATH,
            required=True
        )
    ],
    security=[SecurityRequirement(name="apiKey")],
    responses={
        200: Response(
            description="成功",
            content=ResponseContent(
                content_type=ContentType.JSON,
                model=User
            )
        )
    }
)

# 验证文档
is_valid, errors = builder.validate()
if not is_valid:
    print("验证失败:", errors)

# 生成文档
json_doc = builder.generate_json(output_path="api.json")
yaml_doc = builder.generate_yaml(output_path="api.yaml")
html_doc = builder.generate_html(output_path="api.html")

# 预览文档
builder.preview(port=8080)
```

## API 参考

### 枚举类

- `ParamIn`: 参数位置（QUERY, PATH, HEADER, COOKIE）
- `HttpMethod`: HTTP 方法（GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS, TRACE）
- `SchemaType`: Schema 类型（STRING, INTEGER, NUMBER, BOOLEAN, ARRAY, OBJECT）
- `Format`: 数据格式（EMAIL, DATE, DATE_TIME, URI, UUID, IPV4, IPV6 等）
- `ContentType`: 内容类型（JSON, XML, FORM_URLENCODED, FORM_DATA 等）
- `SecuritySchemeType`: 安全方案类型（API_KEY, HTTP, OAUTH2, OPENID_CONNECT）
- `ApiKeyLocation`: API Key 位置（QUERY, HEADER, COOKIE）

### 模型类

- `Parameter`: 参数定义
- `Field`: 字段定义
- `Schema`: Schema 定义
- `RequestBody`: 请求体定义
- `ResponseContent`: 响应内容定义
- `Response`: 响应定义
- `SecurityScheme`: 安全方案定义
- `SecurityRequirement`: 安全需求定义

### 异常类

- `SwaggerError`: 基础异常类
- `ValidationError`: 验证错误
- `ConfigurationError`: 配置错误
- `ScanError`: 扫描错误
- `ParseError`: 解析错误

## 最佳实践

### 1. 使用装饰器进行自动扫描

```python
# 推荐：使用装饰器，代码更简洁
@swagger_api(path="/api/users", method=HttpMethod.GET, summary="获取用户")
def get_users():
    pass
```

### 2. 使用类型注解自动提取参数

```python
# 推荐：利用类型注解，自动提取参数信息
@swagger_api(path="/api/users/{user_id}", method=HttpMethod.GET)
def get_user(user_id: int, include_profile: bool = False):
    """获取用户详情"""
    pass
```

### 3. 使用 dataclass 定义数据模型

```python
# 推荐：使用 dataclass，自动生成 schema
@dataclass
class User:
    id: int = Field(description="用户ID", example=1)
    name: str = Field(description="用户名", min_length=3, max_length=20)
    email: str = Field(description="邮箱", format=Format.EMAIL)
```

### 4. 使用组件重用减少重复

```python
# 推荐：定义公共组件，多处重用
builder.register_component_schema("User", user_schema)
# 然后在多个接口中引用
```

### 5. 验证文档后再生成

```python
# 推荐：生成前先验证
is_valid, errors = builder.validate()
if is_valid:
    builder.generate_json(output_path="api.json")
else:
    print("验证失败:", errors)
```

## 常见问题

### Q: 如何支持嵌套对象？

A: 使用 dataclass 或手动定义 Schema 的 properties。

```python
@dataclass
class Address:
    street: str
    city: str

@dataclass
class User:
    id: int
    name: str
    address: Address  # 嵌套对象
```

### Q: 如何支持数组类型？

A: 使用 List 类型注解或 Schema with items。

```python
from typing import List

@swagger_api(path="/api/users", method=HttpMethod.GET)
def get_users() -> List[User]:
    pass
```

### Q: 如何支持可选参数？

A: 使用 Optional 类型注解或设置默认值。

```python
from typing import Optional

def get_user(user_id: int, include_profile: Optional[bool] = None):
    pass
```

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 版本历史

- **0.1.0** (当前版本)
  - 初始版本
  - 支持核心功能：接口注册、自动扫描、文档生成
  - 支持 JSON、YAML、HTML 格式
  - 支持安全定义、组件重用
  - 零外部依赖

