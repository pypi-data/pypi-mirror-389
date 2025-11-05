"""配置管理模块"""

import os
import json
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理器，支持从配置文件和环境变量加载配置"""
    
    @staticmethod
    def load_from_file(file_path: str) -> Dict[str, Any]:
        """
        从配置文件加载配置
        
        Args:
            file_path: 配置文件路径（支持 JSON 格式）
        
        Returns:
            配置字典
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.json'):
                return json.load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {file_path}")
    
    @staticmethod
    def load_from_env(prefix: str = "SWAGGER_") -> Dict[str, Any]:
        """
        从环境变量加载配置
        
        Args:
            prefix: 环境变量前缀（默认 "SWAGGER_"）
        
        Returns:
            配置字典
        """
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # 移除前缀并转换为小写
                config_key = key[len(prefix):].lower()
                config[config_key] = value
        
        return config
    
    @staticmethod
    def merge(*configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并多个配置字典
        
        Args:
            *configs: 多个配置字典，后面的会覆盖前面的同名键
        
        Returns:
            合并后的配置字典
        """
        merged = {}
        for config in configs:
            merged.update(config)
        return merged
    
    @staticmethod
    def load(
        config_file: Optional[str] = None,
        env_prefix: str = "SWAGGER_",
        use_env: bool = True
    ) -> Dict[str, Any]:
        """
        加载配置（支持配置文件和环境变量）
        
        Args:
            config_file: 配置文件路径（可选）
            env_prefix: 环境变量前缀
            use_env: 是否使用环境变量
        
        Returns:
            合并后的配置字典
        """
        configs = []
        
        # 从配置文件加载
        if config_file:
            configs.append(ConfigManager.load_from_file(config_file))
        
        # 从环境变量加载
        if use_env:
            env_config = ConfigManager.load_from_env(prefix=env_prefix)
            if env_config:
                configs.append(env_config)
        
        # 合并配置（环境变量优先级更高）
        if configs:
            return ConfigManager.merge(*configs)
        else:
            return {}

