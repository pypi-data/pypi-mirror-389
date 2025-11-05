"""HTML 生成器"""

from typing import Optional
from swagger_sdk.builder import SwaggerBuilder
import json


class HTMLGenerator:
    """HTML 生成器类，生成包含 Swagger UI 的 HTML 文档"""
    
    @staticmethod
    def _generate_swagger_ui_html(openapi_json: dict) -> str:
        """生成包含 Swagger UI 的 HTML"""
        # 将 OpenAPI JSON 嵌入到 HTML 中
        openapi_json_str = json.dumps(openapi_json, ensure_ascii=False, indent=2)
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin: 0;
            padding: 0;
            background: #fafafa;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                spec: {openapi_json_str},
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            }});
        }};
    </script>
</body>
</html>"""
        return html_template
    
    @staticmethod
    def generate(builder: SwaggerBuilder) -> str:
        """生成 HTML 格式文档"""
        from swagger_sdk.json_generator import JSONGenerator
        
        # 先生成 JSON
        openapi_json = JSONGenerator.generate(builder)
        
        # 生成 HTML
        html = HTMLGenerator._generate_swagger_ui_html(openapi_json)
        
        return html

