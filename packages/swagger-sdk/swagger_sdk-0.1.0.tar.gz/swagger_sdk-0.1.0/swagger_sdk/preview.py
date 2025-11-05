"""文档预览功能"""

import http.server
import socketserver
import threading
from typing import Optional
from swagger_sdk.builder import SwaggerBuilder


class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    """预览请求处理器"""
    
    def __init__(self, html_content: bytes, *args, **kwargs):
        self.html_content = html_content
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理 GET 请求"""
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(self.html_content)))
            self.end_headers()
            self.wfile.write(self.html_content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
    
    def log_message(self, format, *args):
        """禁用默认日志输出"""
        pass


class PreviewServer:
    """预览服务器类"""
    
    @staticmethod
    def start(
        builder: SwaggerBuilder,
        port: int = 8080,
        host: str = "localhost"
    ):
        """
        启动预览服务器
        
        Args:
            builder: SwaggerBuilder 实例
            port: 端口号（默认 8080）
            host: 主机地址（默认 localhost）
        """
        # 生成 HTML 内容
        html = builder.generate_html()
        html_bytes = html.encode('utf-8')
        # 创建自定义处理器
        def handler_factory(*args, **kwargs):
            return PreviewHandler(html_bytes, *args, **kwargs)
        
        # 创建服务器
        try:
            with socketserver.TCPServer((host, port), handler_factory) as httpd:
                print(f"预览服务器已启动: http://{host}:{port}")
                print("按 Ctrl+C 停止服务器")
                httpd.serve_forever()
        except OSError as e:
            if "Address already in use" in str(e) or "地址已在使用中" in str(e):
                print(f"错误: 端口 {port} 已被占用，请选择其他端口")
            else:
                print(f"错误: 无法启动服务器 - {e}")

