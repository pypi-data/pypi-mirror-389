# 使用示例和最佳实践

## 示例 0: 配置服务器（Servers）

```python
from swagger_sdk import SwaggerBuilder, HttpMethod

# 方式一：初始化时设置服务器
builder = SwaggerBuilder(
    title="My API",
    version="1.0.0",
    servers=[
        {"url": "https://api.example.com", "description": "生产环境"},
        {"url": "https://staging.example.com", "description": "测试环境"}
    ]
)

# 方式二：使用 add_server 方法添加服务器
builder = SwaggerBuilder(title="My API", version="1.0.0")
builder.add_server("https://api.example.com", description="生产环境")
builder.add_server("https://staging.example.com", description="测试环境")

# 方式三：使用带变量的服务器 URL
builder.add_server(
    "https://{protocol}.example.com:{port}",
    description="可配置的服务器",
    variables={
        "protocol": {
            "default": "api",
            "enum": ["api", "staging", "dev"]
        },
        "port": {
            "default": "443",
            "enum": ["80", "443"]
        }
    }
)

# 方式四：批量设置服务器
builder.set_servers([
    {"url": "https://api1.example.com"},
    {"url": "https://api2.example.com"}
])

# 生成文档
json_doc = builder.generate_json()
# JSON 中将包含 servers 配置
```

## 示例 1: 简单的 REST API

```python
from swagger_sdk import SwaggerBuilder, swagger_api, HttpMethod
from swagger_sdk.models import Parameter, Response, ResponseContent, Schema
from swagger_sdk.enums import ParamIn, SchemaType, ContentType

# 定义接口
@swagger_api(
    path="/api/users",
    method=HttpMethod.GET,
    summary="获取用户列表"
)
def get_users(page: int = 1, size: int = 10):
    """获取用户列表"""
    return {"users": [], "total": 0}

@swagger_api(
    path="/api/users/{user_id}",
    method=HttpMethod.GET,
    summary="获取用户详情"
)
def get_user(user_id: int):
    """获取用户详情"""
    return {"id": user_id, "name": "张三"}

# 创建构建器
builder = SwaggerBuilder(title="用户管理 API", version="1.0.0")

# 扫描接口
builder.scan(__import__(__name__))

# 生成文档
builder.generate_json(output_path="api.json")
builder.generate_html(output_path="api.html")

# 预览
builder.preview()
```

## 示例 2: 使用 dataclass 定义数据模型

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
    age: int

builder = SwaggerBuilder(title="用户 API", version="1.0.0")

builder.register_api(
    path="/api/users",
    method=HttpMethod.POST,
    summary="创建用户",
    request_body=RequestBody(
        required=True,
        model=UserCreate,
        description="用户信息"
    ),
    responses={
        201: Response(
            description="创建成功",
            content=ResponseContent(
                content_type=ContentType.JSON,
                model=UserResponse
            )
        )
    }
)

builder.generate_json(output_path="api.json")
```

## 示例 3: 使用安全定义

```python
from swagger_sdk import SwaggerBuilder, HttpMethod
from swagger_sdk.models import SecurityScheme, SecurityRequirement
from swagger_sdk.enums import SecuritySchemeType, ApiKeyLocation

builder = SwaggerBuilder(title="安全 API", version="1.0.0")

# 注册 API Key 安全方案
api_key = SecurityScheme(
    scheme_type=SecuritySchemeType.API_KEY,
    name="X-API-Key",
    location=ApiKeyLocation.HEADER,
    description="API Key 认证"
)
builder.register_security_scheme("apiKey", api_key)

# 注册 Bearer Token 安全方案
bearer = SecurityScheme(
    scheme_type=SecuritySchemeType.HTTP,
    scheme="bearer",
    bearer_format="JWT",
    description="Bearer Token 认证"
)
builder.register_security_scheme("bearerAuth", bearer)

# 应用安全定义
builder.register_api(
    path="/api/users",
    method=HttpMethod.GET,
    summary="获取用户列表",
    security=[SecurityRequirement(name="apiKey")]
)

builder.register_api(
    path="/api/profile",
    method=HttpMethod.GET,
    summary="获取个人资料",
    security=[SecurityRequirement(name="bearerAuth")]
)

builder.generate_json(output_path="api.json")
```

## 示例 4: 使用组件重用

```python
from swagger_sdk import SwaggerBuilder, HttpMethod
from swagger_sdk.models import Schema, Response, ResponseContent
from swagger_sdk.enums import SchemaType, ContentType

builder = SwaggerBuilder(title="组件 API", version="1.0.0")

# 定义并注册组件
user_schema = Schema(
    schema_type=SchemaType.OBJECT,
    properties={
        "id": Schema(schema_type=SchemaType.INTEGER),
        "name": Schema(schema_type=SchemaType.STRING),
        "email": Schema(schema_type=SchemaType.STRING)
    },
    required=["id", "name", "email"]
)
builder.register_component_schema("User", user_schema)

error_schema = Schema(
    schema_type=SchemaType.OBJECT,
    properties={
        "code": Schema(schema_type=SchemaType.INTEGER),
        "message": Schema(schema_type=SchemaType.STRING)
    },
    required=["code", "message"]
)
builder.register_component_schema("Error", error_schema)

# 在多个接口中引用组件
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
        ),
        400: Response(
            description="错误",
            content=ResponseContent(
                content_type=ContentType.JSON,
                schema=Schema(ref="#/components/schemas/Error")
            )
        )
    }
)

builder.generate_json(output_path="api.json")
```

## 示例 5: 控制器模式

```python
from swagger_sdk import swagger_controller, swagger_api, HttpMethod
from swagger_sdk.models import Parameter, Response, ResponseContent
from swagger_sdk.enums import ParamIn, ContentType

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
    def get_users(self, page: int = 1, size: int = 10):
        """获取用户列表"""
        pass
    
    @swagger_api(
        path="/users/{user_id}",
        method=HttpMethod.GET,
        summary="获取用户详情"
    )
    def get_user(self, user_id: int):
        """获取用户详情"""
        pass
    
    @swagger_api(
        path="/users",
        method=HttpMethod.POST,
        summary="创建用户"
    )
    def create_user(self, data: dict):
        """创建用户"""
        pass

# 扫描控制器
builder = SwaggerBuilder(title="用户 API", version="1.0.0")
builder.scan(__import__(__name__))
builder.generate_json(output_path="api.json")
```

## 示例 6: 完整的 CRUD API

```python
from dataclasses import dataclass
from swagger_sdk import SwaggerBuilder, HttpMethod
from swagger_sdk.models import Parameter, RequestBody, Response, ResponseContent, SecurityScheme, SecurityRequirement, Schema
from swagger_sdk.enums import ParamIn, ContentType, SecuritySchemeType, ApiKeyLocation, SchemaType

@dataclass
class User:
    id: int
    name: str
    email: str

@dataclass
class UserCreate:
    name: str
    email: str

@dataclass
class UserUpdate:
    name: str = None
    email: str = None

builder = SwaggerBuilder(
    title="用户管理 API",
    version="1.0.0",
    description="完整的用户 CRUD 接口"
)

# 注册安全方案
api_key = SecurityScheme(
    scheme_type=SecuritySchemeType.API_KEY,
    name="X-API-Key",
    location=ApiKeyLocation.HEADER
)
builder.register_security_scheme("apiKey", api_key)

# GET /users - 获取用户列表
builder.register_api(
    path="/api/users",
    method=HttpMethod.GET,
    summary="获取用户列表",
    parameters=[
        Parameter(name="page", param_type=int, param_in=ParamIn.QUERY, required=False, default=1),
        Parameter(name="size", param_type=int, param_in=ParamIn.QUERY, required=False, default=10)
    ],
    security=[SecurityRequirement(name="apiKey")],
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

# GET /users/{id} - 获取用户详情
builder.register_api(
    path="/api/users/{user_id}",
    method=HttpMethod.GET,
    summary="获取用户详情",
    parameters=[
        Parameter(name="user_id", param_type=int, param_in=ParamIn.PATH, required=True)
    ],
    security=[SecurityRequirement(name="apiKey")],
    responses={
        200: Response(
            description="成功",
            content=ResponseContent(
                content_type=ContentType.JSON,
                model=User
            )
        ),
        404: Response(description="用户不存在")
    }
)

# POST /users - 创建用户
builder.register_api(
    path="/api/users",
    method=HttpMethod.POST,
    summary="创建用户",
    security=[SecurityRequirement(name="apiKey")],
    request_body=RequestBody(
        required=True,
        model=UserCreate
    ),
    responses={
        201: Response(
            description="创建成功",
            content=ResponseContent(
                content_type=ContentType.JSON,
                model=User
            )
        ),
        400: Response(description="参数错误")
    }
)

# PUT /users/{id} - 更新用户
builder.register_api(
    path="/api/users/{user_id}",
    method=HttpMethod.PUT,
    summary="更新用户",
    parameters=[
        Parameter(name="user_id", param_type=int, param_in=ParamIn.PATH, required=True)
    ],
    security=[SecurityRequirement(name="apiKey")],
    request_body=RequestBody(
        required=True,
        model=UserUpdate
    ),
    responses={
        200: Response(
            description="更新成功",
            content=ResponseContent(
                content_type=ContentType.JSON,
                model=User
            )
        ),
        404: Response(description="用户不存在")
    }
)

# DELETE /users/{id} - 删除用户
builder.register_api(
    path="/api/users/{user_id}",
    method=HttpMethod.DELETE,
    summary="删除用户",
    parameters=[
        Parameter(name="user_id", param_type=int, param_in=ParamIn.PATH, required=True)
    ],
    security=[SecurityRequirement(name="apiKey")],
    responses={
        204: Response(description="删除成功"),
        404: Response(description="用户不存在")
    }
)

# 生成文档
builder.generate_json(output_path="api.json")
builder.generate_yaml(output_path="api.yaml")
builder.generate_html(output_path="api.html")

# 验证
is_valid, errors = builder.validate()
if is_valid:
    print("文档验证通过")
else:
    print("文档验证失败:", errors)
```

## 最佳实践

### 1. 使用类型注解自动提取参数

```python
# ✅ 推荐：使用类型注解
@swagger_api(path="/api/users/{user_id}", method=HttpMethod.GET)
def get_user(user_id: int, include_profile: bool = False):
    """获取用户详情"""
    pass

# ❌ 不推荐：手动定义所有参数
@swagger_api(
    path="/api/users/{user_id}",
    method=HttpMethod.GET,
    parameters=[
        Parameter(name="user_id", param_type=int, param_in=ParamIn.PATH),
        Parameter(name="include_profile", param_type=bool, param_in=ParamIn.QUERY)
    ]
)
def get_user(user_id: int, include_profile: bool = False):
    pass
```

### 2. 使用 dataclass 定义数据模型

```python
# ✅ 推荐：使用 dataclass
@dataclass
class User:
    id: int
    name: str
    email: str

builder.register_api(
    path="/api/users",
    method=HttpMethod.POST,
    request_body=RequestBody(model=User)
)

# ❌ 不推荐：手动定义 Schema
builder.register_api(
    path="/api/users",
    method=HttpMethod.POST,
    request_body=RequestBody(
        schema=Schema(
            schema_type=SchemaType.OBJECT,
            properties={
                "id": Schema(schema_type=SchemaType.INTEGER),
                "name": Schema(schema_type=SchemaType.STRING),
                "email": Schema(schema_type=SchemaType.STRING)
            }
        )
    )
)
```

### 3. 使用组件重用减少重复

```python
# ✅ 推荐：定义组件，多处重用
user_schema = Schema(...)
builder.register_component_schema("User", user_schema)

# 然后在多个接口中引用
schema=Schema(ref="#/components/schemas/User")

# ❌ 不推荐：重复定义相同的 Schema
```

### 4. 使用控制器组织接口

```python
# ✅ 推荐：使用控制器组织相关接口
@swagger_controller(prefix="/api/v1", tags=["用户管理"])
class UserController:
    @swagger_api(path="/users", method=HttpMethod.GET)
    def get_users(self):
        pass

# ❌ 不推荐：分散定义接口
```

### 5. 验证文档后再生成

```python
# ✅ 推荐：先验证再生成
is_valid, errors = builder.validate()
if is_valid:
    builder.generate_json(output_path="api.json")
else:
    print("验证失败:", errors)

# ❌ 不推荐：直接生成，不验证
builder.generate_json(output_path="api.json")
```

