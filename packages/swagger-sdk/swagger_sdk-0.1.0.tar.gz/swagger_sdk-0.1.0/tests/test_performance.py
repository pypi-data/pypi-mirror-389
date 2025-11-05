"""性能测试"""

import unittest
import time
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.models import Parameter, Response, ResponseContent, Schema
from swagger_sdk.enums import HttpMethod, ParamIn, SchemaType, ContentType


class TestPerformance(unittest.TestCase):
    """性能测试"""
    
    def test_scan_performance(self):
        """测试扫描性能"""
        # 创建包含多个接口的模块（模拟）
        builder = SwaggerBuilder(title="Performance Test", version="1.0.0")
        
        # 模拟注册大量接口
        start_time = time.time()
        for i in range(100):
            builder.register_api(
                path=f"/api/resource_{i}",
                method=HttpMethod.GET,
                summary=f"获取资源 {i}",
                parameters=[
                    Parameter(
                        name="id",
                        param_type=int,
                        param_in=ParamIn.PATH,
                        required=True
                    )
                ]
            )
        scan_time = time.time() - start_time
        
        # 验证扫描时间在合理范围内（100个接口应该在1秒内完成）
        self.assertLess(scan_time, 1.0, f"扫描100个接口耗时 {scan_time:.3f} 秒，超过预期")
        print(f"扫描100个接口耗时: {scan_time:.3f} 秒")
    
    def test_json_generation_performance(self):
        """测试 JSON 生成性能"""
        builder = SwaggerBuilder(title="Performance Test", version="1.0.0")
        
        # 注册多个接口
        for i in range(50):
            builder.register_api(
                path=f"/api/resource_{i}",
                method=HttpMethod.GET,
                summary=f"获取资源 {i}",
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
        
        # 测试生成性能
        start_time = time.time()
        json_doc = builder.generate_json()
        generation_time = time.time() - start_time
        
        # 验证生成时间在合理范围内（50个接口应该在0.5秒内完成）
        self.assertLess(generation_time, 0.5, f"生成JSON耗时 {generation_time:.3f} 秒，超过预期")
        print(f"生成50个接口的JSON耗时: {generation_time:.3f} 秒")
        self.assertIn("paths", json_doc)
        self.assertEqual(len(json_doc["paths"]), 50)
    
    def test_yaml_generation_performance(self):
        """测试 YAML 生成性能"""
        builder = SwaggerBuilder(title="Performance Test", version="1.0.0")
        
        # 注册多个接口
        for i in range(50):
            builder.register_api(
                path=f"/api/resource_{i}",
                method=HttpMethod.GET,
                summary=f"获取资源 {i}"
            )
        
        # 测试生成性能
        start_time = time.time()
        yaml_doc = builder.generate_yaml()
        generation_time = time.time() - start_time
        
        # 验证生成时间在合理范围内
        self.assertLess(generation_time, 0.5, f"生成YAML耗时 {generation_time:.3f} 秒，超过预期")
        print(f"生成50个接口的YAML耗时: {generation_time:.3f} 秒")
        self.assertIn("paths:", yaml_doc)
    
    def test_html_generation_performance(self):
        """测试 HTML 生成性能"""
        builder = SwaggerBuilder(title="Performance Test", version="1.0.0")
        
        # 注册多个接口
        for i in range(50):
            builder.register_api(
                path=f"/api/resource_{i}",
                method=HttpMethod.GET,
                summary=f"获取资源 {i}"
            )
        
        # 测试生成性能
        start_time = time.time()
        html_doc = builder.generate_html()
        generation_time = time.time() - start_time
        
        # 验证生成时间在合理范围内
        self.assertLess(generation_time, 1.0, f"生成HTML耗时 {generation_time:.3f} 秒，超过预期")
        print(f"生成50个接口的HTML耗时: {generation_time:.3f} 秒")
        self.assertIn("<!DOCTYPE html>", html_doc)
    
    def test_validation_performance(self):
        """测试验证性能"""
        builder = SwaggerBuilder(title="Performance Test", version="1.0.0")
        
        # 注册多个接口
        for i in range(100):
            builder.register_api(
                path=f"/api/resource_{i}",
                method=HttpMethod.GET,
                summary=f"获取资源 {i}"
            )
        
        # 测试验证性能
        start_time = time.time()
        is_valid, errors = builder.validate()
        validation_time = time.time() - start_time
        
        # 验证验证时间在合理范围内
        self.assertLess(validation_time, 0.5, f"验证100个接口耗时 {validation_time:.3f} 秒，超过预期")
        print(f"验证100个接口耗时: {validation_time:.3f} 秒")
        self.assertTrue(is_valid)
    
    def test_batch_register_performance(self):
        """测试批量注册性能"""
        builder = SwaggerBuilder(title="Performance Test", version="1.0.0")
        
        # 准备批量注册数据
        apis = [
            {
                "path": f"/api/resource_{i}",
                "method": HttpMethod.GET,
                "summary": f"获取资源 {i}"
            }
            for i in range(100)
        ]
        
        # 测试批量注册性能
        start_time = time.time()
        builder.register_apis(apis)
        register_time = time.time() - start_time
        
        # 验证注册时间在合理范围内
        self.assertLess(register_time, 0.5, f"批量注册100个接口耗时 {register_time:.3f} 秒，超过预期")
        print(f"批量注册100个接口耗时: {register_time:.3f} 秒")
        self.assertEqual(len(builder.apis), 100)

