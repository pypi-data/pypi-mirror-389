"""装饰器测试"""

import unittest
from swagger_sdk.decorators import swagger_api, swagger_controller
from swagger_sdk.enums import HttpMethod
from swagger_sdk.models import Parameter, Response
from swagger_sdk.enums import ParamIn


class TestSwaggerApiDecorator(unittest.TestCase):
    """@swagger_api 装饰器测试"""
    
    def test_swagger_api_basic(self):
        """测试 @swagger_api 装饰器基本功能"""
        @swagger_api(
            path="/api/users",
            method=HttpMethod.GET,
            summary="获取用户列表"
        )
        def get_users():
            """获取用户列表"""
            return {"users": []}
        
        # 验证函数仍然可以正常调用
        result = get_users()
        self.assertEqual(result, {"users": []})
        
        # 验证装饰器添加了元数据
        self.assertTrue(hasattr(get_users, '_swagger_api'))
        api_info = get_users._swagger_api
        self.assertEqual(api_info["path"], "/api/users")
        self.assertEqual(api_info["method"], HttpMethod.GET)
        self.assertEqual(api_info["summary"], "获取用户列表")
    
    def test_swagger_api_with_parameters(self):
        """测试带参数的装饰器"""
        @swagger_api(
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
        def get_user(user_id: int):
            return {"id": user_id}
        
        # 验证函数可以正常调用
        result = get_user(123)
        self.assertEqual(result, {"id": 123})
        
        # 验证元数据包含参数
        api_info = get_user._swagger_api
        self.assertEqual(len(api_info["parameters"]), 1)
        self.assertEqual(api_info["parameters"][0].name, "user_id")
    
    def test_swagger_api_with_responses(self):
        """测试带响应的装饰器"""
        @swagger_api(
            path="/api/users",
            method=HttpMethod.POST,
            summary="创建用户",
            responses={
                201: Response(description="创建成功")
            }
        )
        def create_user():
            return {"id": 1}
        
        # 验证元数据包含响应
        api_info = create_user._swagger_api
        self.assertIn("responses", api_info)
        self.assertIn(201, api_info["responses"])


class TestSwaggerControllerDecorator(unittest.TestCase):
    """@swagger_controller 装饰器测试"""
    
    def test_swagger_controller_basic(self):
        """测试 @swagger_controller 装饰器基本功能"""
        @swagger_controller(
            prefix="/api/users",
            tags=["用户管理"],
            description="用户管理相关接口"
        )
        class UserController:
            pass
        
        # 验证类有装饰器元数据
        self.assertTrue(hasattr(UserController, '_swagger_controller'))
        controller_info = UserController._swagger_controller
        self.assertEqual(controller_info["prefix"], "/api/users")
        self.assertEqual(controller_info["tags"], ["用户管理"])
        self.assertEqual(controller_info["description"], "用户管理相关接口")
    
    def test_swagger_controller_with_methods(self):
        """测试控制器类中的方法"""
        @swagger_controller(prefix="/api/users")
        class UserController:
            @swagger_api(
                path="/",
                method=HttpMethod.GET,
                summary="获取用户列表"
            )
            def get_users(self):
                return []
            
            @swagger_api(
                path="/{user_id}",
                method=HttpMethod.GET,
                summary="获取用户详情"
            )
            def get_user(self, user_id: int):
                return {"id": user_id}
        
        # 验证类有控制器元数据
        self.assertTrue(hasattr(UserController, '_swagger_controller'))
        
        # 验证方法有API元数据
        self.assertTrue(hasattr(UserController.get_users, '_swagger_api'))
        self.assertTrue(hasattr(UserController.get_user, '_swagger_api'))
        
        # 验证方法可以正常调用
        controller = UserController()
        users = controller.get_users()
        self.assertEqual(users, [])
        
        user = controller.get_user(123)
        self.assertEqual(user, {"id": 123})

