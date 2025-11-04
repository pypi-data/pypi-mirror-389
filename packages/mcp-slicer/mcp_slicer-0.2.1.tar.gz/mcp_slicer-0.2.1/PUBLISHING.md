# 使用 uv 打包并发布到 PyPI

本指南说明如何使用 `uv` 打包 mcp-slicer 项目并发布到 PyPI。

## 前提条件

1. **PyPI 账户**

   - 在 [PyPI](https://pypi.org/account/register/) 注册账户
   - 在 [TestPyPI](https://test.pypi.org/account/register/) 注册测试账户（用于测试发布）

2. **安装必要的工具**

   ```bash
   # 确保已安装 uv
   uv --version
   ```

3. **配置认证令牌**
   - 登录 PyPI，进入 Account Settings > API tokens
   - 创建一个新的 API token（推荐使用项目级别的 token）
   - 保存 token，后续发布时会用到

## 发布流程

### 步骤 1: 更新版本号

在 `pyproject.toml` 中更新版本号：

```toml
[project]
name = "mcp-slicer"
version = "0.1.3"  # 更新版本号
```

**版本号规则**（遵循语义化版本）：

- `MAJOR.MINOR.PATCH`
- `0.1.2` → `0.1.3` (补丁版本：bug 修复)
- `0.1.2` → `0.2.0` (次要版本：新功能，向后兼容)
- `0.1.2` → `1.0.0` (主要版本：破坏性变更)

### 步骤 2: 确保代码和文档是最新的

```bash
# 确保所有更改已提交
git status

# 更新 README（如果需要）
# 确保 README.md 和 README_zh.md 是最新的

# 运行测试（如果有）
# uv run pytest
```

### 步骤 3: 清理旧的构建文件

```bash
# 清理之前的构建
rm -rf dist/
rm -rf build/
rm -rf *.egg-info
```

### 步骤 4: 使用 uv 构建包

使用 `uv` 构建分发包：

```bash
# 方式 1: 使用 uv build（推荐）
uv build

# 方式 2: 使用 uv pip install build 然后 build
uv pip install build
python -m build
```

构建完成后，会在 `dist/` 目录生成：

- `mcp_slicer-X.X.X-py3-none-any.whl` (wheel 格式)
- `mcp_slicer-X.X.X.tar.gz` (源码分发包)

### 步骤 5: 验证构建的包（可选）

`uv publish` 会自动验证包的有效性，无需额外检查。如果需要手动验证，可以：

```bash
# 测试安装构建的包
uv pip install dist/mcp_slicer-*.whl
```

### 步骤 6: 测试安装（可选但推荐）

在发布前，测试构建的包是否可以正常安装：

```bash
# 创建一个测试虚拟环境
uv venv test-env

# Windows
test-env\Scripts\activate
# Linux/Mac
source test-env/bin/activate

# 从本地安装
uv pip install dist/mcp_slicer-*.whl

# 测试是否正常工作
mcp-slicer --help

# 清理测试环境
deactivate
rm -rf test-env
```

### 步骤 7: 发布到 TestPyPI（推荐）

首先发布到 TestPyPI 进行测试：

```bash
# 使用 uv 发布到 TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/ dist/*
```

**认证方式**：

- 使用 API token：当提示输入用户名和密码时，用户名填 `__token__`，密码填你的 API token

**验证 TestPyPI 发布**：

```bash
# 从 TestPyPI 安装测试
uv pip install --index-url https://test.pypi.org/simple/ mcp-slicer
```

### 步骤 8: 发布到正式 PyPI

确认 TestPyPI 测试无误后，发布到正式 PyPI：

```bash
# 使用 uv 发布
uv publish dist/*
```

**注意**：

- 发布到正式 PyPI 后，版本号不能更改或删除
- 确保版本号是唯一的（不能重复发布相同版本）

### 步骤 9: 验证发布

1. **检查 PyPI 页面**：
   访问 https://pypi.org/project/mcp-slicer/ 确认包已发布

2. **测试安装**：

   ```bash
   # 从 PyPI 安装
   uv pip install mcp-slicer

   # 或使用 uvx 测试
   uvx mcp-slicer --help
   ```

3. **更新 GitHub 标签**（可选）：
   ```bash
   # 创建 git tag
   git tag v0.1.3
   git push origin v0.1.3
   ```

## 使用 uv 的完整命令示例

### 一键发布流程

```bash
# 1. 更新版本号后，清理并构建
rm -rf dist/ build/ *.egg-info
uv build

# 2. 发布到 TestPyPI（测试）
uv publish --publish-url https://test.pypi.org/legacy/ dist/*

# 3. 测试安装
uv pip install --index-url https://test.pypi.org/simple/ mcp-slicer

# 4. 发布到正式 PyPI
uv publish dist/*
```

## 配置自动化发布（可选）

### 使用 GitHub Actions

创建 `.github/workflows/publish.yml`：

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        run: uv python install 3.13

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

## 常见问题

### 问题 1: 认证失败

**解决方案**：

- 确保 API token 正确
- 用户名使用 `__token__`
- 检查 token 是否有正确的权限

### 问题 2: 版本号已存在

**错误信息**：`File already exists`

**解决方案**：

- 更新 `pyproject.toml` 中的版本号
- 重新构建和发布

### 问题 3: 构建失败

**可能原因**：

- `pyproject.toml` 配置错误
- 缺少必要的文件（如 README.md）

**解决方案**：

```bash
# 检查配置
uv build --check

# 查看详细错误信息
uv build --verbose
```

### 问题 4: 依赖问题

**解决方案**：

- 确保 `pyproject.toml` 中的依赖版本正确
- 使用 `uv lock` 更新锁文件

## 发布检查清单

发布前确认：

- [ ] 版本号已更新
- [ ] `pyproject.toml` 配置正确
- [ ] README.md 是最新的
- [ ] 所有测试通过（如果有）
- [ ] 代码已提交到 Git
- [ ] 已清理旧的构建文件
- [ ] 构建成功且无错误
- [ ] 已测试从 TestPyPI 安装
- [ ] PyPI API token 已准备好

## 更多资源

- [uv 发布文档](https://docs.astral.sh/uv/publishing/)
- [PyPI 官方文档](https://packaging.python.org/en/latest/)
- [Python 打包指南](https://packaging.python.org/guides/distributing-packages-using-setuptools/)
- [语义化版本](https://semver.org/)

## 快速参考

```bash
# 构建包
uv build

# 发布到 TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/ dist/*

# 发布到 PyPI
uv publish dist/*

# 从 PyPI 安装
uv pip install mcp-slicer

# 使用 uvx 运行
uvx mcp-slicer
```
