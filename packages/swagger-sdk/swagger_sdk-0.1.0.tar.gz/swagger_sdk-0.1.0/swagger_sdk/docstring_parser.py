"""文档字符串解析器"""

import re
from typing import Dict, Optional


class DocstringParser:
    """文档字符串解析器，支持 Google 风格和简单格式"""
    
    @staticmethod
    def parse(docstring: Optional[str]) -> Dict[str, any]:
        """
        解析文档字符串
        
        Args:
            docstring: 文档字符串
        
        Returns:
            解析结果字典，包含：
            - summary: 摘要
            - Args: 参数字典 {参数名: 描述}
            - Returns: 返回值描述
        """
        if not docstring:
            return {"summary": ""}
        
        # 清理文档字符串
        docstring = docstring.strip()
        
        result = {
            "summary": "",
            "Args": {},
            "Returns": ""
        }
        
        # 按段落分割
        lines = docstring.split('\n')
        
        # 提取摘要（第一段，直到遇到 Args/Returns 等关键字）
        summary_lines = []
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if summary_lines and not current_section:
                    # 摘要结束，遇到空行
                    continue
                elif current_section and section_content:
                    # 段落结束，处理当前段落
                    DocstringParser._process_section(result, current_section, '\n'.join(section_content))
                    section_content = []
                continue
            
            # 检查是否是新的章节
            if line.lower() in ['args:', 'arguments:', 'parameters:']:
                if summary_lines and not result["summary"]:
                    result["summary"] = ' '.join(summary_lines).strip()
                current_section = "Args"
                section_content = []
                continue
            elif line.lower() in ['returns:', 'return:']:
                if summary_lines and not result["summary"]:
                    result["summary"] = ' '.join(summary_lines).strip()
                current_section = "Returns"
                section_content = []
                continue
            elif line.lower() in ['raises:', 'exceptions:', 'yields:', 'yield:']:
                if summary_lines and not result["summary"]:
                    result["summary"] = ' '.join(summary_lines).strip()
                current_section = None  # 暂时不支持这些章节
                section_content = []
                continue
            
            # 收集内容
            if current_section:
                section_content.append(line)
            else:
                summary_lines.append(line)
        
        # 处理最后一段
        if summary_lines and not result["summary"]:
            result["summary"] = ' '.join(summary_lines).strip()
        
        if current_section and section_content:
            DocstringParser._process_section(result, current_section, '\n'.join(section_content))
        
        return result
    
    @staticmethod
    def _process_section(result: Dict, section: str, content: str):
        """处理特定章节的内容"""
        if section == "Args":
            # 解析参数
            # Google 风格格式：参数名: 描述
            # 支持多行描述（缩进）
            lines = content.split('\n')
            current_param = None
            current_desc = []
            
            for line in lines:
                # 检查是否是参数定义行（包含冒号）
                if ':' in line and not line.startswith(' '):
                    # 保存上一个参数
                    if current_param:
                        result["Args"][current_param] = ' '.join(current_desc).strip()
                    
                    # 开始新参数
                    parts = line.split(':', 1)
                    current_param = parts[0].strip()
                    current_desc = [parts[1].strip()] if len(parts) > 1 else []
                else:
                    # 续行描述
                    if current_param:
                        current_desc.append(line.strip())
            
            # 保存最后一个参数
            if current_param:
                result["Args"][current_param] = ' '.join(current_desc).strip()
        
        elif section == "Returns":
            # 返回值描述
            result["Returns"] = content.strip()

