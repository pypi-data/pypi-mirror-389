"""装饰器实现"""

from typing import Callable, Any, Optional, List, Dict
from swagger_sdk.enums import HttpMethod
from swagger_sdk.models import Parameter, RequestBody, Response


def swagger_api(
    path: str,
    method: HttpMethod,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    parameters: Optional[List[Parameter]] = None,
    request_body: Optional[RequestBody] = None,
    responses: Optional[Dict[int, Response]] = None,
    **kwargs
):
    """
    函数级别装饰器，用于标记 API 接口
    
    Args:
        path: 接口路径
        method: HTTP 方法
        summary: 接口摘要
        description: 接口描述
        tags: 标签列表
        parameters: 参数列表
        request_body: 请求体
        responses: 响应定义
        **kwargs: 其他参数
    """
    def decorator(func: Callable) -> Callable:
        # 保存原始函数信息
        func._swagger_api = {
            "path": path,
            "method": method,
            "summary": summary,
            "description": description,
            "tags": tags or [],
            "parameters": parameters or [],
            "request_body": request_body,
            "responses": responses or {},
            "handler": func,
            **kwargs
        }
        return func
    return decorator


def swagger_controller(
    prefix: str = "",
    tags: Optional[List[str]] = None,
    description: Optional[str] = None,
    **kwargs
):
    """
    类级别装饰器，用于标记控制器类
    
    Args:
        prefix: 路径前缀
        tags: 标签列表
        description: 描述
        **kwargs: 其他参数
    """
    def decorator(cls: type) -> type:
        # 保存控制器信息
        cls._swagger_controller = {
            "prefix": prefix,
            "tags": tags or [],
            "description": description,
            **kwargs
        }
        return cls
    return decorator

