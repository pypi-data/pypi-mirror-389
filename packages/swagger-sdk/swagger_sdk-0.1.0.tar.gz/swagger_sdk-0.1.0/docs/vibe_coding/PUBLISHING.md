# 发布指南

本文档说明如何将 swagger-sdk 发布到 PyPI。

## 前置准备

1. **注册 PyPI 账号**
   - 在 [PyPI](https://pypi.org/account/register/) 注册账号
   - 在 [TestPyPI](https://test.pypi.org/account/register/) 注册测试账号（可选，用于测试发布）

2. **安装发布工具**
   ```bash
   pip install build twine
   ```

3. **配置 PyPI 凭据**
   - 创建 `~/.pypirc` 文件（Linux/Mac）或配置环境变量
   - 或者使用 `twine upload` 时输入用户名和密码

## 发布步骤

### 1. 更新版本号

在 `swagger_sdk/__init__.py` 中更新版本号：
```python
__version__ = "0.1.0"  # 更新为新版本号
```

### 2. 更新 pyproject.toml

确保 `pyproject.toml` 中的版本号与 `__init__.py` 一致。

### 3. 清理旧的构建文件

```bash
rm -rf build/ dist/ *.egg-info
```

### 4. 构建分发包

```bash
# 使用现代构建工具（推荐）
python -m build

# 或者使用 setuptools（旧方式）
python setup.py sdist bdist_wheel
```

### 5. 检查分发包

```bash
# 检查分发包内容
twine check dist/*
```

### 6. 测试发布（推荐）

先发布到 TestPyPI 进行测试：

```bash
# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 测试安装
pip install --index-url https://test.pypi.org/simple/ swagger-sdk
```

### 7. 正式发布

```bash
# 上传到 PyPI
twine upload dist/*
```

### 8. 验证安装

```bash
# 等待几分钟后，测试安装
pip install swagger-sdk

# 验证导入
python -c "from swagger_sdk import SwaggerBuilder; print('Success!')"
```

## 发布检查清单

- [ ] 版本号已更新
- [ ] `pyproject.toml` 中的元数据已更新（作者、URL等）
- [ ] `README.md` 已完善
- [ ] `LICENSE` 文件已添加
- [ ] 所有测试通过：`pytest tests/`
- [ ] 代码已通过 lint 检查
- [ ] 构建成功：`python -m build`
- [ ] 分发包检查通过：`twine check dist/*`
- [ ] 在 TestPyPI 测试安装成功
- [ ] 已准备好发布到 PyPI

## 版本号规则

遵循 [语义化版本](https://semver.org/lang/zh-CN/)：

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

示例：
- `0.1.0` - 初始版本
- `0.1.1` - Bug 修复
- `0.2.0` - 新功能
- `1.0.0` - 稳定版本

## 常见问题

### 1. 上传时提示 "This filename already exists"

说明该版本已发布，需要更新版本号。

### 2. 上传失败：认证错误

检查：
- `~/.pypirc` 配置是否正确
- 用户名和密码是否正确
- 是否使用了 API token（推荐）

### 3. 安装后无法导入

检查：
- 包名是否正确（`swagger-sdk` vs `swagger_sdk`）
- 是否等待了足够的时间（PyPI 索引更新需要时间）
- 尝试强制重新安装：`pip install --force-reinstall swagger-sdk`

## PyPI API Token（推荐）

1. 在 PyPI 账号设置中创建 API Token
2. 使用 token 上传：
   ```bash
   twine upload -u __token__ -p <your-token> dist/*
   ```

## 自动化发布（可选）

可以使用 GitHub Actions 自动化发布流程，参考 `.github/workflows/publish.yml`（如果存在）。

