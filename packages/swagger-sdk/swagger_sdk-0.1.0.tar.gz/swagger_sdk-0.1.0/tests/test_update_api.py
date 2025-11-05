"""接口更新功能测试"""

import unittest
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.models import Parameter
from swagger_sdk.enums import HttpMethod, ParamIn


class TestUpdateAPI(unittest.TestCase):
    """接口更新功能测试"""
    
    def test_update_api_existing(self):
        """测试更新已存在的接口"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        # 注册初始接口
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户"
        )
        
        # 更新接口
        builder.update_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表",
            description="获取所有用户的列表"
        )
        
        # 验证接口已更新
        self.assertEqual(len(builder.apis), 1)
        api = builder.apis[0]
        self.assertEqual(api["summary"], "获取用户列表")
        self.assertEqual(api["description"], "获取所有用户的列表")
    
    def test_update_api_add_parameters(self):
        """测试更新接口时添加参数"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        # 注册初始接口
        builder.register_api(
            path="/api/users/{user_id}",
            method=HttpMethod.GET,
            summary="获取用户详情"
        )
        
        # 更新接口，添加参数
        builder.update_api(
            path="/api/users/{user_id}",
            method=HttpMethod.GET,
            parameters=[
                Parameter(
                    name="user_id",
                    param_type=int,
                    param_in=ParamIn.PATH,
                    required=True
                )
            ]
        )
        
        # 验证参数已添加
        api = builder.apis[0]
        self.assertEqual(len(api["parameters"]), 1)
        self.assertEqual(api["parameters"][0].name, "user_id")
    
    def test_update_api_replace_parameters(self):
        """测试更新接口时替换参数"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        # 注册初始接口，带参数
        builder.register_api(
            path="/api/users/{user_id}",
            method=HttpMethod.GET,
            summary="获取用户详情",
            parameters=[
                Parameter(
                    name="user_id",
                    param_type=int,
                    param_in=ParamIn.PATH,
                    required=True
                )
            ]
        )
        
        # 更新接口，替换参数
        builder.update_api(
            path="/api/users/{user_id}",
            method=HttpMethod.GET,
            parameters=[
                Parameter(
                    name="user_id",
                    param_type=str,
                    param_in=ParamIn.PATH,
                    required=True
                ),
                Parameter(
                    name="include_profile",
                    param_type=bool,
                    param_in=ParamIn.QUERY,
                    required=False
                )
            ]
        )
        
        # 验证参数已替换
        api = builder.apis[0]
        self.assertEqual(len(api["parameters"]), 2)
        param_names = [p.name for p in api["parameters"]]
        self.assertIn("user_id", param_names)
        self.assertIn("include_profile", param_names)
    
    def test_update_api_not_found(self):
        """测试更新不存在的接口（应该创建新接口）"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        # 尝试更新不存在的接口
        builder.update_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表"
        )
        
        # 应该创建新接口
        self.assertEqual(len(builder.apis), 1)
        api = builder.apis[0]
        self.assertEqual(api["path"], "/api/users")
        self.assertEqual(api["method"], HttpMethod.GET)
    
    def test_update_api_partial(self):
        """测试部分更新接口（只更新部分字段）"""
        builder = SwaggerBuilder(title="Test API", version="1.0.0")
        
        # 注册初始接口
        builder.register_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户",
            description="原始描述",
            tags=["users"]
        )
        
        # 只更新 summary
        builder.update_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表"
        )
        
        # 验证只更新了 summary，其他字段保持不变
        api = builder.apis[0]
        self.assertEqual(api["summary"], "获取用户列表")
        self.assertEqual(api["description"], "原始描述")
        self.assertEqual(api["tags"], ["users"])

