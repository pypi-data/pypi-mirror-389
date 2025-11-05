# 发布检查清单

在发布到 PyPI 之前，请完成以下检查：

## ✅ 已完成的文件

- [x] `pyproject.toml` - 现代 Python 包配置
- [x] `setup.py` - 兼容性构建脚本
- [x] `MANIFEST.in` - 包含文件清单
- [x] `LICENSE` - MIT 许可证
- [x] `README.md` - 项目文档（已更新安装说明）
- [x] `CHANGELOG.md` - 更新日志
- [x] `PUBLISHING.md` - 发布指南
- [x] `.gitignore` - Git 忽略文件
- [x] `check_build.py` - 构建检查脚本

## ⚠️ 需要手动更新的信息

### 1. 更新作者信息

**在 `pyproject.toml` 中：**
```toml
authors = [
    {name = "你的真实姓名", email = "your.real.email@example.com"},
]
```

**在 `setup.py` 中：**
```python
author="你的真实姓名",
author_email="your.real.email@example.com",
```

### 2. 更新项目 URL

**在 `pyproject.toml` 中：**
```toml
[project.urls]
Homepage = "https://github.com/yourusername/swagger-sdk"
Documentation = "https://github.com/yourusername/swagger-sdk#readme"
Repository = "https://github.com/yourusername/swagger-sdk"
Issues = "https://github.com/yourusername/swagger-sdk/issues"
```

**在 `setup.py` 中：**
```python
url="https://github.com/yourusername/swagger-sdk",
```

### 3. 更新 README.md 中的仓库链接

在 README.md 中找到所有 `<repository-url>` 并替换为实际的 GitHub 仓库地址。

## 📋 发布步骤

### 步骤 1: 运行检查脚本

```bash
python check_build.py
```

确保所有检查通过（元数据检查会提示需要更新作者信息）。

### 步骤 2: 更新元数据

按照上面的说明更新 `pyproject.toml` 和 `setup.py` 中的作者和 URL 信息。

### 步骤 3: 安装构建工具

```bash
pip install build twine
```

### 步骤 4: 清理旧的构建文件

```bash
# Windows
rmdir /s /q build dist *.egg-info 2>nul

# Linux/Mac
rm -rf build/ dist/ *.egg-info
```

### 步骤 5: 构建分发包

```bash
python -m build
```

这将创建：
- `dist/swagger-sdk-0.1.0.tar.gz` (源码分发包)
- `dist/swagger_sdk-0.1.0-py3-none-any.whl` (wheel 分发包)

### 步骤 6: 检查分发包

```bash
twine check dist/*
```

应该看到类似输出：
```
Checking dist/swagger-sdk-0.1.0.tar.gz: PASSED
Checking dist/swagger_sdk-0.1.0-py3-none-any.whl: PASSED
```

### 步骤 7: 测试发布（推荐）

先发布到 TestPyPI 进行测试：

```bash
twine upload --repository testpypi dist/*
```

然后测试安装：
```bash
pip install --index-url https://test.pypi.org/simple/ swagger-sdk
```

### 步骤 8: 正式发布到 PyPI

```bash
twine upload dist/*
```

### 步骤 9: 验证安装

等待几分钟后（PyPI 索引更新需要时间），测试安装：

```bash
pip install swagger-sdk
python -c "from swagger_sdk import SwaggerBuilder; print('Success!')"
```

## 📝 发布后事项

1. **创建 Git Tag**
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. **创建 GitHub Release**
   - 在 GitHub 仓库页面创建新的 Release
   - 使用版本号 `v0.1.0` 作为标签
   - 添加发布说明（可以从 `CHANGELOG.md` 复制）

3. **更新文档**
   - 确保 README.md 中的安装说明正确
   - 更新示例代码中的版本号（如果需要）

## 🔍 常见问题

### Q: 上传时提示 "This filename already exists"
A: 该版本已存在，需要更新版本号。更新 `swagger_sdk/__init__.py` 和 `pyproject.toml` 中的版本号。

### Q: 如何创建 PyPI API Token？
A: 
1. 登录 [PyPI](https://pypi.org)
2. 进入 Account settings → API tokens
3. 创建新的 API token
4. 使用 token 上传：
   ```bash
   twine upload -u __token__ -p <your-token> dist/*
   ```

### Q: 安装后无法导入？
A: 检查：
- 包名是否正确（`swagger-sdk` 安装后导入为 `swagger_sdk`）
- 等待几分钟让 PyPI 索引更新
- 尝试强制重新安装：`pip install --force-reinstall swagger-sdk`

## 📚 相关文档

- [PUBLISHING.md](PUBLISHING.md) - 详细的发布指南
- [CHANGELOG.md](CHANGELOG.md) - 版本更新日志

