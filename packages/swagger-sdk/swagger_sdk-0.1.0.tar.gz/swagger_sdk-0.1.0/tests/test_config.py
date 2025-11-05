"""配置管理功能测试"""

import unittest
import os
import tempfile
import json
from swagger_sdk.config import ConfigManager


class TestConfigManager(unittest.TestCase):
    """配置管理功能测试"""
    
    def test_load_from_json_file(self):
        """测试从 JSON 配置文件加载配置"""
        config_data = {
            "title": "Test API",
            "version": "1.0.0",
            "description": "测试API",
            "tags": ["api", "test"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = ConfigManager.load_from_file(temp_path)
            
            self.assertEqual(config["title"], "Test API")
            self.assertEqual(config["version"], "1.0.0")
            self.assertEqual(config["description"], "测试API")
            self.assertIn("tags", config)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_load_from_env_variables(self):
        """测试从环境变量加载配置"""
        # 设置环境变量
        os.environ["SWAGGER_TITLE"] = "Env API"
        os.environ["SWAGGER_VERSION"] = "2.0.0"
        os.environ["SWAGGER_DESCRIPTION"] = "从环境变量加载的API"
        
        try:
            config = ConfigManager.load_from_env(prefix="SWAGGER_")
            
            self.assertEqual(config["title"], "Env API")
            self.assertEqual(config["version"], "2.0.0")
            self.assertEqual(config["description"], "从环境变量加载的API")
        finally:
            # 清理环境变量
            os.environ.pop("SWAGGER_TITLE", None)
            os.environ.pop("SWAGGER_VERSION", None)
            os.environ.pop("SWAGGER_DESCRIPTION", None)
    
    def test_merge_configs(self):
        """测试合并多个配置源"""
        config1 = {"title": "API", "version": "1.0.0"}
        config2 = {"description": "描述", "version": "2.0.0"}
        
        merged = ConfigManager.merge(config1, config2)
        
        # config2 应该覆盖 config1 的同名键
        self.assertEqual(merged["title"], "API")
        self.assertEqual(merged["version"], "2.0.0")
        self.assertEqual(merged["description"], "描述")
    
    def test_load_from_env_with_prefix(self):
        """测试带前缀的环境变量加载"""
        os.environ["MYAPP_API_TITLE"] = "My API"
        os.environ["MYAPP_API_VERSION"] = "3.0.0"
        
        try:
            config = ConfigManager.load_from_env(prefix="MYAPP_API_")
            
            self.assertEqual(config["title"], "My API")
            self.assertEqual(config["version"], "3.0.0")
        finally:
            os.environ.pop("MYAPP_API_TITLE", None)
            os.environ.pop("MYAPP_API_VERSION", None)

