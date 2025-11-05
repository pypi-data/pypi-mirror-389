"""批量注册接口功能测试"""

import unittest
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.models import Parameter
from swagger_sdk.enums import HttpMethod, ParamIn


class TestBatchRegister(unittest.TestCase):
    """批量注册接口功能测试"""
    
    def test_register_multiple_apis(self):
        """测试批量注册多个接口"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        apis = [
            {
                "path": "/api/users",
                "method": HttpMethod.GET,
                "summary": "获取用户列表"
            },
            {
                "path": "/api/users/{user_id}",
                "method": HttpMethod.GET,
                "summary": "获取用户详情",
                "parameters": [
                    Parameter(
                        name="user_id",
                        param_type=int,
                        param_in=ParamIn.PATH,
                        required=True
                    )
                ]
            },
            {
                "path": "/api/users",
                "method": HttpMethod.POST,
                "summary": "创建用户"
            }
        ]
        
        builder.register_apis(apis)
        
        # 验证所有接口都已注册
        self.assertEqual(len(builder.apis), 3)
        
        # 验证接口内容
        paths = {api["path"]: api for api in builder.apis}
        self.assertIn("/api/users", paths)
        
        # 验证 GET /api/users
        get_apis = [api for api in builder.apis if api["path"] == "/api/users" and api["method"] == HttpMethod.GET]
        self.assertEqual(len(get_apis), 1)
        self.assertEqual(get_apis[0]["summary"], "获取用户列表")
        
        # 验证 POST /api/users
        post_apis = [api for api in builder.apis if api["path"] == "/api/users" and api["method"] == HttpMethod.POST]
        self.assertEqual(len(post_apis), 1)
        self.assertEqual(post_apis[0]["summary"], "创建用户")
    
    def test_register_apis_with_defaults(self):
        """测试批量注册时使用默认值"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        apis = [
            {
                "path": "/api/users",
                "method": HttpMethod.GET,
                "summary": "获取用户列表"
            },
            {
                "path": "/api/posts",
                "method": HttpMethod.GET,
                "summary": "获取文章列表"
            }
        ]
        
        # 使用默认的 tags
        default_tags = ["default"]
        builder.register_apis(apis, tags=default_tags)
        
        # 验证所有接口都有默认的 tags
        for api in builder.apis:
            self.assertIn("default", api.get("tags", []))
    
    def test_register_apis_empty_list(self):
        """测试批量注册空列表"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        builder.register_apis([])
        
        self.assertEqual(len(builder.apis), 0)

