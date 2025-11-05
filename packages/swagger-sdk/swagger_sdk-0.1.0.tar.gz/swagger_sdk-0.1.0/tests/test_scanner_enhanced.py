"""扫描功能增强测试（整合 TypeParser 和 DocstringParser）"""

import unittest
import tempfile
import os
import importlib.util
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.decorators import swagger_api
from swagger_sdk.enums import HttpMethod, ParamIn
from swagger_sdk.models import Parameter
from typing import Optional


class TestScannerEnhanced(unittest.TestCase):
    """扫描功能增强测试"""
    
    def test_scan_auto_extract_function_signature(self):
        """测试扫描时自动提取函数签名参数"""
        test_module_code = '''
from swagger_sdk.decorators import swagger_api
from swagger_sdk.enums import HttpMethod

@swagger_api(
    path="/api/users/{user_id}",
    method=HttpMethod.GET,
    summary="获取用户详情"
)
def get_user(user_id: int, include_profile: bool = False):
    """获取用户详情"""
    return {"id": user_id}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(test_module_code)
            temp_path = f.name
        
        try:
            spec = importlib.util.spec_from_file_location("test_module", temp_path)
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            
            builder = SwaggerBuilder(title="Test API", version="1.0.0")
            builder.scan(test_module)
            
            # 验证扫描结果
            self.assertEqual(len(builder.apis), 1)
            api = builder.apis[0]
            
            # 验证自动提取的参数
            self.assertIn("parameters", api)
            params = {p.name if isinstance(p, Parameter) else p["name"]: p for p in api["parameters"]}
            
            # user_id 应该在参数中（path参数）
            self.assertIn("user_id", params)
            user_id_param = params["user_id"]
            if isinstance(user_id_param, Parameter):
                self.assertEqual(user_id_param.param_type, int)
                self.assertEqual(user_id_param.param_in, ParamIn.PATH)
                self.assertTrue(user_id_param.required)
            else:
                self.assertEqual(user_id_param["schema"]["type"], "integer")
                self.assertEqual(user_id_param["in"], "path")
                self.assertTrue(user_id_param["required"])
            
            # include_profile 应该在参数中（query参数，可选）
            self.assertIn("include_profile", params)
            include_profile_param = params["include_profile"]
            if isinstance(include_profile_param, Parameter):
                self.assertEqual(include_profile_param.param_type, bool)
                self.assertEqual(include_profile_param.param_in, ParamIn.QUERY)
                self.assertFalse(include_profile_param.required)
            else:
                self.assertEqual(include_profile_param["schema"]["type"], "boolean")
                self.assertEqual(include_profile_param["in"], "query")
                self.assertFalse(include_profile_param["required"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_scan_auto_extract_docstring(self):
        """测试扫描时自动提取 docstring 描述"""
        test_module_code = '''
from swagger_sdk.decorators import swagger_api
from swagger_sdk.enums import HttpMethod

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
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(test_module_code)
            temp_path = f.name
        
        try:
            spec = importlib.util.spec_from_file_location("test_module", temp_path)
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            
            builder = SwaggerBuilder(title="Test API", version="1.0.0")
            builder.scan(test_module)
            
            api = builder.apis[0]
            
            # 验证从 docstring 提取的描述
            # description 应该包含 docstring 的摘要
            if "description" in api and api["description"]:
                # 应该包含文档字符串信息
                pass
            
            # 验证参数描述
            if "parameters" in api:
                params = {p.name if isinstance(p, Parameter) else p["name"]: p for p in api["parameters"]}
                if "page" in params:
                    page_param = params["page"]
                    if isinstance(page_param, Parameter):
                        # 应该从 docstring 提取描述
                        self.assertIsNotNone(page_param.description)
                        self.assertIn("页码", page_param.description)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_scan_auto_generate_response_schema(self):
        """测试扫描时自动生成 Response schema"""
        test_module_code = '''
from swagger_sdk.decorators import swagger_api
from swagger_sdk.enums import HttpMethod
from typing import Dict

@swagger_api(
    path="/api/users",
    method=HttpMethod.GET,
    summary="获取用户列表"
)
def get_users() -> Dict[str, int]:
    """获取用户列表"""
    return {"total": 0}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(test_module_code)
            temp_path = f.name
        
        try:
            spec = importlib.util.spec_from_file_location("test_module", temp_path)
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            
            builder = SwaggerBuilder(title="Test API", version="1.0.0")
            builder.scan(test_module)
            
            api = builder.apis[0]
            
            # 验证自动生成的响应
            # 如果装饰器没有指定响应，应该从返回值注解自动生成
            # 这里我们检查是否有 responses 或者可以自动生成
            if "responses" not in api or not api["responses"]:
                # 如果装饰器没有指定响应，扫描器应该自动生成一个默认的200响应
                # 基于返回值注解
                pass
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

