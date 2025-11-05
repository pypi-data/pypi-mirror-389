"""SwaggerBuilder 类实现"""

from typing import Optional, List, Dict, Any, Callable
from swagger_sdk.enums import HttpMethod
from swagger_sdk.models import Parameter, RequestBody, Response, SecurityRequirement, SecurityScheme, Schema


class SwaggerBuilder:
    """Swagger 文档构建器"""
    
    def __init__(
        self,
        title: str,
        version: str,
        description: Optional[str] = None,
        servers: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        """
        初始化 Swagger 构建器
        
        Args:
            title: API 标题
            version: API 版本
            description: API 描述（可选）
            servers: 服务器列表，每个元素是一个字典，包含 url（必需）和可选的 description、variables
            **kwargs: 其他配置参数
        """
        self.title = title
        self.version = version
        self.description = description
        self.apis: List[Dict[str, Any]] = []
        # Components 用于存储可重用的组件
        self.components: Dict[str, Dict[str, Any]] = {
            "schemas": {},
            "securitySchemes": {}
        }
        # Servers 配置
        self.servers: List[Dict[str, Any]] = servers or []
        # 存储其他配置
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def register_component_schema(self, name: str, schema: Schema):
        """
        注册 schema 组件
        
        Args:
            name: 组件名称
            schema: Schema 对象
        """
        self.components["schemas"][name] = schema
    
    def register_security_scheme(self, name: str, scheme: SecurityScheme):
        """
        注册安全方案
        
        Args:
            name: 安全方案名称
            scheme: SecurityScheme 对象
        """
        self.components["securitySchemes"][name] = scheme
    
    def add_server(self, url: str, description: Optional[str] = None, variables: Optional[Dict[str, Any]] = None):
        """
        添加服务器配置
        
        Args:
            url: 服务器 URL（必需）
            description: 服务器描述（可选）
            variables: 服务器变量（可选），用于 URL 模板中的变量替换
        """
        server = {"url": url}
        if description:
            server["description"] = description
        if variables:
            server["variables"] = variables
        self.servers.append(server)
    
    def set_servers(self, servers: List[Dict[str, Any]]):
        """
        设置服务器列表
        
        Args:
            servers: 服务器列表，每个元素是一个字典，包含 url（必需）和可选的 description、variables
        """
        self.servers = servers
    
    def register_api(
        self,
        path: str,
        method: HttpMethod,
        handler: Optional[Callable] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        parameters: Optional[List[Parameter]] = None,
        request_body: Optional[RequestBody] = None,
        responses: Optional[Dict[int, Response]] = None,
        security: Optional[List[SecurityRequirement]] = None,
        **kwargs
    ):
        """
        手动注册接口
        
        Args:
            path: 接口路径
            method: HTTP 方法（使用 HttpMethod 枚举）
            handler: 处理函数（可选）
            summary: 接口摘要
            description: 接口描述
            tags: 标签列表
            parameters: 参数列表，每个参数为 Parameter 实例
            request_body: 请求体定义，RequestBody 实例
            responses: 响应定义，key 为状态码（int），value 为 Response 实例
            security: 安全需求列表，每个元素为 SecurityRequirement 实例
            **kwargs: 其他参数
        """
        api_info = {
            "path": path,
            "method": method,
            "summary": summary,
            "description": description,
            "tags": tags or [],
            "parameters": parameters or [],
            "request_body": request_body,
            "responses": responses or {},
            "security": security or [],
            **kwargs
        }
        
        if handler is not None:
            api_info["handler"] = handler
        
        self.apis.append(api_info)
    
    def register_apis(self, apis: List[Dict[str, Any]], **defaults):
        """
        批量注册接口
        
        Args:
            apis: 接口列表，每个元素是一个字典，包含接口信息
            **defaults: 默认参数，会应用到所有接口
        """
        for api_dict in apis:
            # 合并默认参数
            api_params = {**defaults, **api_dict}
            
            # 提取必需参数
            path = api_params.pop("path")
            method = api_params.pop("method")
            handler = api_params.pop("handler", None)
            
            # 其他参数传递给 register_api
            self.register_api(
                path=path,
                method=method,
                handler=handler,
                **api_params
            )
    
    def update_api(
        self,
        path: str,
        method: HttpMethod,
        **updates
    ):
        """
        更新已注册的接口
        
        Args:
            path: 接口路径
            method: HTTP 方法
            **updates: 要更新的字段
        """
        # 查找已存在的接口
        for i, api in enumerate(self.apis):
            if api.get("path") == path and api.get("method") == method:
                # 更新接口信息
                for key, value in updates.items():
                    if value is not None:  # 只更新非 None 的值
                        if key in ["parameters", "responses", "tags"]:
                            # 对于列表和字典，直接替换
                            api[key] = value
                        else:
                            api[key] = value
                return
        
        # 如果接口不存在，创建新接口
        self.register_api(path=path, method=method, **updates)
    
    def scan(self, module_or_path, pattern: Optional[str] = None, **kwargs):
        """
        扫描模块中的注解接口
        
        Args:
            module_or_path: 模块对象或模块路径（字符串）
            pattern: 扫描模式（可选）
            **kwargs: 其他参数
        """
        from swagger_sdk.scanner import Scanner
        
        # 如果是字符串，尝试导入模块
        if isinstance(module_or_path, str):
            import importlib
            module = importlib.import_module(module_or_path)
        else:
            module = module_or_path
        
        Scanner.scan_module(self, module)
    
    def generate_json(self, output_path: Optional[str] = None) -> dict:
        """
        生成 JSON 格式文档
        
        Args:
            output_path: 输出文件路径（可选，如果提供则保存到文件）
        
        Returns:
            OpenAPI 3.0 规范的字典
        """
        from swagger_sdk.json_generator import JSONGenerator
        
        openapi_doc = JSONGenerator.generate(self)
        
        if output_path:
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(openapi_doc, f, ensure_ascii=False, indent=2)
        
        return openapi_doc
    
    def generate_yaml(self, output_path: Optional[str] = None) -> str:
        """
        生成 YAML 格式文档
        
        Args:
            output_path: 输出文件路径（可选）
        
        Returns:
            YAML 格式的字符串
        """
        from swagger_sdk.yaml_generator import YAMLGenerator
        
        yaml_str = YAMLGenerator.generate(self)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(yaml_str)
        
        return yaml_str
    
    def generate_html(self, output_path: Optional[str] = None, template: Optional[str] = None) -> str:
        """
        生成 HTML 格式文档
        
        Args:
            output_path: 输出文件路径（可选）
            template: 自定义模板（可选，暂未实现）
        
        Returns:
            HTML 格式的字符串
        """
        from swagger_sdk.html_generator import HTMLGenerator
        
        html = HTMLGenerator.generate(self)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
        
        return html
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        验证文档规范
        
        Returns:
            (是否有效, 错误列表)
        """
        from swagger_sdk.validator import Validator
        return Validator.validate(self)
    
    def preview(self, port: int = 8080, host: str = "localhost"):
        """
        启动预览服务器
        
        Args:
            port: 端口号（默认 8080）
            host: 主机地址（默认 localhost）
        """
        from swagger_sdk.preview import PreviewServer
        PreviewServer.start(self, port=port, host=host)

