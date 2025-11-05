# API 参考文档

## SwaggerBuilder

### `__init__(title: str, version: str, description: Optional[str] = None, servers: Optional[List[Dict[str, Any]]] = None, **kwargs)`

初始化 Swagger 构建器。

**参数：**
- `title` (str): API 标题
- `version` (str): API 版本
- `description` (Optional[str]): API 描述
- `servers` (Optional[List[Dict[str, Any]]]): 服务器列表，每个元素是一个字典，包含 url（必需）和可选的 description、variables
- `**kwargs`: 其他配置参数

**示例：**
```python
builder = SwaggerBuilder(
    title="My API",
    version="1.0.0",
    description="My API description",
    servers=[
        {"url": "https://api.example.com", "description": "生产环境"}
    ]
)
```

### `register_api(path: str, method: HttpMethod, handler: Optional[Callable] = None, summary: Optional[str] = None, description: Optional[str] = None, tags: Optional[List[str]] = None, parameters: Optional[List[Parameter]] = None, request_body: Optional[RequestBody] = None, responses: Optional[Dict[int, Response]] = None, security: Optional[List[SecurityRequirement]] = None, **kwargs)`

手动注册单个接口。

**参数：**
- `path` (str): 接口路径
- `method` (HttpMethod): HTTP 方法
- `handler` (Optional[Callable]): 处理函数
- `summary` (Optional[str]): 接口摘要
- `description` (Optional[str]): 接口描述
- `tags` (Optional[List[str]]): 标签列表
- `parameters` (Optional[List[Parameter]]): 参数列表
- `request_body` (Optional[RequestBody]): 请求体定义
- `responses` (Optional[Dict[int, Response]]): 响应定义
- `security` (Optional[List[SecurityRequirement]]): 安全需求列表

**示例：**
```python
builder.register_api(
    path="/api/users",
    method=HttpMethod.GET,
    summary="获取用户列表"
)
```

### `register_apis(apis: List[Dict[str, Any]], **defaults)`

批量注册接口。

**参数：**
- `apis` (List[Dict[str, Any]]): 接口列表
- `**defaults`: 默认参数，会应用到所有接口

**示例：**
```python
apis = [
    {"path": "/api/users", "method": HttpMethod.GET, "summary": "获取用户"},
    {"path": "/api/posts", "method": HttpMethod.GET, "summary": "获取文章"}
]
builder.register_apis(apis, tags=["默认标签"])
```

### `update_api(path: str, method: HttpMethod, **updates)`

更新已注册的接口。

**参数：**
- `path` (str): 接口路径
- `method` (HttpMethod): HTTP 方法
- `**updates`: 要更新的字段

**示例：**
```python
builder.update_api(
    path="/api/users",
    method=HttpMethod.GET,
    description="更新后的描述"
)
```

### `register_component_schema(name: str, schema: Schema)`

注册 schema 组件。

**参数：**
- `name` (str): 组件名称
- `schema` (Schema): Schema 对象

**示例：**
```python
user_schema = Schema(
    schema_type=SchemaType.OBJECT,
    properties={"id": Schema(schema_type=SchemaType.INTEGER)}
)
builder.register_component_schema("User", user_schema)
```

### `register_security_scheme(name: str, scheme: SecurityScheme)`

注册安全方案。

**参数：**
- `name` (str): 安全方案名称
- `scheme` (SecurityScheme): SecurityScheme 对象

**示例：**
```python
scheme = SecurityScheme(
    scheme_type=SecuritySchemeType.API_KEY,
    name="X-API-Key",
    location=ApiKeyLocation.HEADER
)
builder.register_security_scheme("apiKey", scheme)
```

### `add_server(url: str, description: Optional[str] = None, variables: Optional[Dict[str, Any]] = None)`

添加服务器配置。

**参数：**
- `url` (str): 服务器 URL（必需）
- `description` (Optional[str]): 服务器描述（可选）
- `variables` (Optional[Dict[str, Any]]): 服务器变量（可选），用于 URL 模板中的变量替换

**示例：**
```python
# 简单服务器
builder.add_server("https://api.example.com", description="生产环境")

# 带变量的服务器
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
```

### `set_servers(servers: List[Dict[str, Any]])`

设置服务器列表。

**参数：**
- `servers` (List[Dict[str, Any]]): 服务器列表，每个元素是一个字典，包含 url（必需）和可选的 description、variables

**示例：**
```python
builder.set_servers([
    {"url": "https://api.example.com", "description": "生产环境"},
    {"url": "https://staging.example.com", "description": "测试环境"}
])
```

### `scan(module_or_path, pattern: Optional[str] = None, **kwargs)`

扫描模块中的装饰器接口。

**参数：**
- `module_or_path`: 模块对象或模块路径
- `pattern` (Optional[str]): 扫描模式（未实现）
- `**kwargs`: 其他参数

**示例：**
```python
builder.scan(__import__(__name__))
```

### `generate_json(output_path: Optional[str] = None) -> Dict[str, Any]`

生成 JSON 格式文档。

**参数：**
- `output_path` (Optional[str]): 输出文件路径

**返回：**
- `Dict[str, Any]`: OpenAPI JSON 文档

**示例：**
```python
json_doc = builder.generate_json(output_path="api.json")
```

### `generate_yaml(output_path: Optional[str] = None) -> str`

生成 YAML 格式文档。

**参数：**
- `output_path` (Optional[str]): 输出文件路径

**返回：**
- `str`: YAML 格式字符串

**示例：**
```python
yaml_doc = builder.generate_yaml(output_path="api.yaml")
```

### `generate_html(output_path: Optional[str] = None, template: Optional[str] = None) -> str`

生成 HTML 格式文档。

**参数：**
- `output_path` (Optional[str]): 输出文件路径
- `template` (Optional[str]): 自定义模板（未实现）

**返回：**
- `str`: HTML 格式字符串

**示例：**
```python
html_doc = builder.generate_html(output_path="api.html")
```

### `validate() -> Tuple[bool, List[str]]`

验证文档规范。

**返回：**
- `Tuple[bool, List[str]]`: (是否有效, 错误列表)

**示例：**
```python
is_valid, errors = builder.validate()
```

### `preview(port: int = 8080, host: str = "localhost")`

启动预览服务器。

**参数：**
- `port` (int): 端口号（默认 8080）
- `host` (str): 主机地址（默认 localhost）

**示例：**
```python
builder.preview(port=8080)
```

## Parameter

参数定义类。

**属性：**
- `name` (str): 参数名称
- `param_type` (Type): 参数类型
- `param_in` (ParamIn): 参数位置
- `required` (bool): 是否必填
- `description` (Optional[str]): 参数描述
- `default` (Any): 默认值
- `example` (Any): 示例值
- `enum` (Optional[List]): 枚举值
- `format` (Optional[Format]): 格式约束
- `min_value` (Any): 最小值
- `max_value` (Any): 最大值
- `pattern` (Optional[str]): 正则表达式
- `min_length` (Optional[int]): 最小长度
- `max_length` (Optional[int]): 最大长度

**示例：**
```python
Parameter(
    name="user_id",
    param_type=int,
    param_in=ParamIn.PATH,
    required=True,
    description="用户ID",
    example=123
)
```

## Schema

Schema 定义类。

**属性：**
- `schema_type` (SchemaType): Schema 类型
- `description` (Optional[str]): 描述
- `default` (Any): 默认值
- `example` (Any): 示例值
- `enum` (Optional[List]): 枚举值
- `format` (Optional[Format]): 格式
- `items` (Optional[Schema]): 数组元素 Schema
- `properties` (Optional[Dict[str, Schema]]): 对象属性
- `required` (Optional[List[str]]): 必填字段列表
- `ref` (Optional[str]): 引用路径

**示例：**
```python
Schema(
    schema_type=SchemaType.OBJECT,
    properties={
        "id": Schema(schema_type=SchemaType.INTEGER),
        "name": Schema(schema_type=SchemaType.STRING)
    },
    required=["id", "name"]
)
```

## SecurityScheme

安全方案定义类。

**属性：**
- `scheme_type` (SecuritySchemeType): 安全方案类型
- `description` (Optional[str]): 描述
- `name` (Optional[str]): API Key 名称（用于 API_KEY 类型）
- `location` (Optional[ApiKeyLocation]): API Key 位置（用于 API_KEY 类型）
- `scheme` (Optional[str]): HTTP 认证方案（用于 HTTP 类型，如 "bearer", "basic"）
- `bearer_format` (Optional[str]): Bearer Token 格式（用于 HTTP 类型，如 "JWT"）
- `flows` (Optional[Dict[str, Any]]): OAuth2 流程配置（用于 OAUTH2 类型）
- `open_id_connect_url` (Optional[str]): OpenID Connect URL（用于 OPENID_CONNECT 类型）

**示例：**
```python
# API Key
SecurityScheme(
    scheme_type=SecuritySchemeType.API_KEY,
    name="X-API-Key",
    location=ApiKeyLocation.HEADER
)

# Bearer Token
SecurityScheme(
    scheme_type=SecuritySchemeType.HTTP,
    scheme="bearer",
    bearer_format="JWT"
)
```

## SecurityRequirement

安全需求定义类（用于在接口中应用安全方案）。

**属性：**
- `name` (str): 安全方案名称（在 Components 中注册的名称）
- `scopes` (Optional[List[str]]): OAuth2 作用域列表（仅用于 OAuth2 安全方案）

**示例：**
```python
SecurityRequirement(name="apiKey")
SecurityRequirement(name="oauth2", scopes=["read", "write"])
```

## 装饰器

### `@swagger_api(path: str, method: HttpMethod, summary: Optional[str] = None, description: Optional[str] = None, tags: Optional[List[str]] = None, parameters: Optional[List[Parameter]] = None, request_body: Optional[RequestBody] = None, responses: Optional[Dict[int, Response]] = None, security: Optional[List[SecurityRequirement]] = None, **kwargs)`

函数级别装饰器，用于标记 API 接口。

**参数：**
- `path` (str): 接口路径
- `method` (HttpMethod): HTTP 方法
- `summary` (Optional[str]): 接口摘要
- `description` (Optional[str]): 接口描述
- `tags` (Optional[List[str]]): 标签列表
- `parameters` (Optional[List[Parameter]]): 参数列表
- `request_body` (Optional[RequestBody]): 请求体定义
- `responses` (Optional[Dict[int, Response]]): 响应定义
- `security` (Optional[List[SecurityRequirement]]): 安全需求列表

### `@swagger_controller(prefix: str = "", tags: Optional[List[str]] = None, description: Optional[str] = None, **kwargs)`

类级别装饰器，用于标记控制器类。

**参数：**
- `prefix` (str): 路径前缀
- `tags` (Optional[List[str]]): 标签列表
- `description` (Optional[str]): 控制器描述

