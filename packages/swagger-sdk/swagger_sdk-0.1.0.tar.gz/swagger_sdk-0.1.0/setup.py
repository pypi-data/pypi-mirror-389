"""Setup script for swagger-sdk package"""

from setuptools import setup, find_packages
import os

# 读取 README 文件
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# 读取版本号
def get_version():
    init_path = os.path.join(os.path.dirname(__file__), "swagger_sdk", "__init__.py")
    with open(init_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"

setup(
    name="swagger-sdk",
    version=get_version(),
    description="一个独立、灵活的 Python SDK，用于自动生成符合 OpenAPI 3.0 规范的 Swagger 文档",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="songxulin",
    author_email="songandco99@gmail.com",
    url="https://github.com/AndsGo/swagger-sdk",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Documentation",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    keywords=["swagger", "openapi", "api", "documentation", "openapi3", "swagger-ui"],
    zip_safe=False,
    include_package_data=True,
)

