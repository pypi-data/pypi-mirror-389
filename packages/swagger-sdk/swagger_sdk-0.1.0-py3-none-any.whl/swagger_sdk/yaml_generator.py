"""YAML 生成器"""

from typing import Dict, Any, List
from swagger_sdk.builder import SwaggerBuilder
from swagger_sdk.json_generator import JSONGenerator


class YAMLGenerator:
    """YAML 生成器类，将 OpenAPI JSON 转换为 YAML 格式"""
    
    @staticmethod
    def _escape_string(value: Any) -> str:
        """转义字符串值"""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            # 检查是否需要引号
            if any(char in value for char in ['{', '}', '[', ']', ':', ',', '&', '*', '#', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`']):
                # 转义特殊字符
                value = value.replace('"', '\\"')
                return f'"{value}"'
            return value
        return str(value)
    
    @staticmethod
    def _indent(text: str, level: int) -> str:
        """添加缩进"""
        indent_str = "  " * level  # 2个空格
        lines = text.split('\n')
        indented_lines = []
        for line in lines:
            if line.strip():  # 非空行
                indented_lines.append(indent_str + line)
            else:
                indented_lines.append("")  # 保留空行
        return '\n'.join(indented_lines)
    
    @staticmethod
    def _to_yaml_value(value: Any, indent_level: int = 0) -> str:
        """将值转换为 YAML 格式"""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # 检查是否需要多行字符串
            if '\n' in value:
                # 使用 | 表示多行字符串
                lines = value.split('\n')
                result = "|\n"
                for line in lines:
                    result += "  " * (indent_level + 1) + line + "\n"
                return result.rstrip()
            else:
                # 检查是否需要引号
                if any(char in value for char in [':', '{', '}', '[', ']', ',', '&', '*', '#', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`']):
                    value = value.replace('"', '\\"')
                    return f'"{value}"'
                return value
        elif isinstance(value, dict):
            if not value:
                return "{}"
            result = "\n"
            for key, val in value.items():
                key_str = YAMLGenerator._escape_string(key)
                val_str = YAMLGenerator._to_yaml_value(val, indent_level + 1)
                if isinstance(val, (dict, list)):
                    result += "  " * (indent_level + 1) + f"{key_str}:{val_str}\n"
                else:
                    result += "  " * (indent_level + 1) + f"{key_str}: {val_str}\n"
            return result.rstrip()
        elif isinstance(value, list):
            if not value:
                return "[]"
            result = "\n"
            for item in value:
                item_str = YAMLGenerator._to_yaml_value(item, indent_level + 1)
                if isinstance(item, (dict, list)):
                    result += "  " * (indent_level + 1) + f"-{item_str}\n"
                else:
                    result += "  " * (indent_level + 1) + f"- {item_str}\n"
            return result.rstrip()
        else:
            return str(value)
    
    @staticmethod
    def _dict_to_yaml(data: Dict[str, Any], indent_level: int = 0) -> str:
        """将字典转换为 YAML 字符串"""
        lines = []
        
        for key, value in data.items():
            key_str = YAMLGenerator._escape_string(key)
            
            if isinstance(value, dict):
                if not value:
                    lines.append("  " * indent_level + f"{key_str}: {{}}")
                else:
                    lines.append("  " * indent_level + f"{key_str}:")
                    lines.append(YAMLGenerator._dict_to_yaml(value, indent_level + 1))
            elif isinstance(value, list):
                if not value:
                    lines.append("  " * indent_level + f"{key_str}: []")
                else:
                    lines.append("  " * indent_level + f"{key_str}:")
                    for item in value:
                        if isinstance(item, dict):
                            # 列表中的字典项，第一行应该是 "- key: value" 格式
                            first_key = True
                            for item_key, item_val in item.items():
                                item_key_str = YAMLGenerator._escape_string(item_key)
                                if first_key:
                                    # 第一行：- key: value
                                    item_val_str = YAMLGenerator._to_yaml_value(item_val, indent_level + 1)
                                    if isinstance(item_val, (dict, list)):
                                        lines.append("  " * (indent_level + 1) + f"- {item_key_str}:{item_val_str}")
                                    else:
                                        lines.append("  " * (indent_level + 1) + f"- {item_key_str}: {item_val_str}")
                                    first_key = False
                                else:
                                    # 后续行：  key: value（多缩进2个空格）
                                    item_val_str = YAMLGenerator._to_yaml_value(item_val, indent_level + 2)
                                    if isinstance(item_val, (dict, list)):
                                        lines.append("  " * (indent_level + 2) + f"{item_key_str}:{item_val_str}")
                                    else:
                                        lines.append("  " * (indent_level + 2) + f"{item_key_str}: {item_val_str}")
                        else:
                            item_str = YAMLGenerator._to_yaml_value(item, indent_level + 1)
                            lines.append("  " * (indent_level + 1) + f"- {item_str}")
            else:
                value_str = YAMLGenerator._to_yaml_value(value, indent_level)
                lines.append("  " * indent_level + f"{key_str}: {value_str}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def generate(builder: SwaggerBuilder) -> str:
        """生成 YAML 格式文档"""
        # 先生成 JSON
        json_doc = JSONGenerator.generate(builder)
        
        # 转换为 YAML
        yaml_str = YAMLGenerator._dict_to_yaml(json_doc, 0)
        
        return yaml_str

