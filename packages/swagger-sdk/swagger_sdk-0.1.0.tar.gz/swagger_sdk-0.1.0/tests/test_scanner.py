"""扫描功能测试"""

import unittest
import sys
import os
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.decorators import swagger_api, swagger_controller
from swagger_sdk.enums import HttpMethod


# 创建测试模块
def create_test_module():
    """创建测试模块"""
    test_module_code = '''
from swagger_sdk.decorators import swagger_api
from swagger_sdk.enums import HttpMethod

@swagger_api(
    path="/api/test",
    method=HttpMethod.GET,
    summary="测试接口"
)
def test_function():
    """测试函数"""
    return {"message": "test"}
'''
    
    # 创建临时测试模块
    test_module_path = os.path.join(os.path.dirname(__file__), 'test_module.py')
    with open(test_module_path, 'w', encoding='utf-8') as f:
        f.write(test_module_code)
    
    return test_module_path


class TestScanner(unittest.TestCase):
    """扫描功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.builder = SwaggerBuilder(title="Test API", version="1.0.0")
    
    def test_scan_module_with_decorated_function(self):
        """测试扫描模块中的装饰器函数"""
        # 创建测试模块
        test_module_code = '''
from swagger_sdk.decorators import swagger_api
from swagger_sdk.enums import HttpMethod

@swagger_api(
    path="/api/test",
    method=HttpMethod.GET,
    summary="测试接口"
)
def test_function():
    """测试函数"""
    return {"message": "test"}

@swagger_api(
    path="/api/users",
    method=HttpMethod.POST,
    summary="创建用户"
)
def create_user():
    return {"id": 1}
'''
        
        # 写入临时文件
        import tempfile
        import importlib.util
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(test_module_code)
            temp_path = f.name
        
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location("test_module", temp_path)
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            
            # 扫描模块
            self.builder.scan(test_module)
            
            # 验证扫描结果
            self.assertEqual(len(self.builder.apis), 2)
            
            # 按路径查找接口（不依赖顺序）
            paths = {api["path"]: api for api in self.builder.apis}
            
            # 验证第一个接口
            api1 = paths["/api/test"]
            self.assertEqual(api1["method"], HttpMethod.GET)
            self.assertEqual(api1["summary"], "测试接口")
            
            # 验证第二个接口
            api2 = paths["/api/users"]
            self.assertEqual(api2["method"], HttpMethod.POST)
            self.assertEqual(api2["summary"], "创建用户")
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_scan_class_with_decorated_methods(self):
        """测试扫描类中的装饰器方法"""
        # 创建测试模块
        test_module_code = '''
from swagger_sdk.decorators import swagger_api, swagger_controller
from swagger_sdk.enums import HttpMethod

@swagger_controller(prefix="/api/users", tags=["用户管理"])
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
'''
        
        import tempfile
        import importlib.util
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(test_module_code)
            temp_path = f.name
        
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location("test_module", temp_path)
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            
            # 扫描模块
            self.builder.scan(test_module)
            
            # 验证扫描结果
            self.assertEqual(len(self.builder.apis), 2)
            
            # 按路径查找接口（不依赖顺序）
            paths = {api["path"]: api for api in self.builder.apis}
            
            # 验证第一个接口（应该包含prefix）
            api1 = paths["/api/users/"]
            self.assertEqual(api1["method"], HttpMethod.GET)
            self.assertEqual(api1["summary"], "获取用户列表")
            self.assertIn("用户管理", api1["tags"])
            
            # 验证第二个接口
            api2 = paths["/api/users/{user_id}"]
            self.assertEqual(api2["method"], HttpMethod.GET)
            self.assertEqual(api2["summary"], "获取用户详情")
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

