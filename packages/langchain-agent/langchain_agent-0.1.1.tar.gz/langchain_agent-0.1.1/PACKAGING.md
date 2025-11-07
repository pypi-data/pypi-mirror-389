# 📦 打包与发布指南

本文档介绍如何打包和发布 `langchain_agent` 项目。

## 📋 目录

- [准备工作](#准备工作)
- [构建包](#构建包)
- [本地测试](#本地测试)
- [发布到 PyPI](#发布到-pypi)
- [版本管理](#版本管理)
- [故障排除](#故障排除)

## 🔧 准备工作

### 1. 安装构建工具

```bash
# 使用 uv (推荐)
uv pip install --upgrade build twine

# 或使用传统 pip
pip install --upgrade build twine
```

### 2. 配置 PyPI 凭据

创建 `~/.pypirc` 文件（可以从项目根目录的 `.pypirc.example` 复制）:

```bash
cp .pypirc.example ~/.pypirc
```

编辑 `~/.pypirc` 并填入你的 API token:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

**获取 API Token:**
- PyPI: https://pypi.org/manage/account/token/
- TestPyPI: https://test.pypi.org/manage/account/token/

### 3. 更新版本号

在 `pyproject.toml` 中更新版本号:

```toml
[project]
version = "0.2.0"  # 更新为新版本
```

### 4. 更新 CHANGELOG

在 `CHANGELOG.md` 中记录更改:

```markdown
## [0.2.0] - 2024-01-15

### Added
- 新功能描述

### Changed
- 更改描述

### Fixed
- 修复描述
```

## 🏗️ 构建包

### 方式一: 使用 Make 命令（推荐）

```bash
# 清理旧的构建文件
make clean-build

# 构建包
make build

# 检查包的有效性
make build-check
```

### 方式二: 使用脚本

```bash
# 直接运行构建脚本
./scripts/build.sh
```

### 方式三: 手动构建

```bash
# 清理旧文件
rm -rf build/ dist/ *.egg-info

# 使用 build 工具构建
python -m build

# 或使用 uv
uv run python -m build
```

构建完成后，`dist/` 目录将包含:
- `langchain_agent-0.1.0.tar.gz` (源代码分发包)
- `langchain_agent-0.1.0-py3-none-any.whl` (wheel 包)

## 🧪 本地测试

### 1. 安装开发版本

```bash
# 使用 Make 命令 (推荐)
make install-local

# 或使用 uv
uv pip install -e .

# 或使用传统 pip
pip install -e .
```

### 2. 从构建包安装

```bash
# 使用 Make 命令 (推荐)
make install-from-build

# 或使用 uv
uv pip install dist/langchain_agent-*.whl --force-reinstall

# 或使用传统 pip
pip install dist/langchain_agent-*.whl --force-reinstall
```

### 3. 测试安装的包

```bash
# 运行命令行工具
langchain-chat

# 或在 Python 中导入
python -c "from langchain_agent import ChatAgent; print('导入成功')"
```

### 4. 运行测试

```bash
# 运行所有测试
make test

# 生成覆盖率报告
make coverage
```

## 🚀 发布到 PyPI

### 发布前检查清单

运行发布前检查:

```bash
make check-version
```

确认以下事项:
- [ ] 已更新版本号
- [ ] 已更新 CHANGELOG.md
- [ ] 所有测试通过
- [ ] 代码已提交到 Git
- [ ] 已清理构建目录
- [ ] 已构建新包并通过检查

### 完整的发布前准备

```bash
# 一键运行所有发布前检查和构建
make pre-release
```

这个命令会依次执行:
1. 清理构建文件 (`clean-build`)
2. 运行测试 (`test`)
3. 检查版本 (`check-version`)
4. 构建包 (`build`)
5. 检查包有效性 (`build-check`)

### 发布到 TestPyPI（推荐先测试）

```bash
# 发布到测试服务器
make publish-test

# 或使用脚本
./scripts/publish.sh testpypi
```

测试安装:

```bash
# 使用 uv (推荐)
uv pip install -i https://test.pypi.org/simple/ langchain-agent

# 或使用传统 pip
pip install -i https://test.pypi.org/simple/ langchain-agent

# 测试功能
langchain-chat
```

### 发布到正式 PyPI

⚠️ **注意**: 发布到 PyPI 后无法删除，请确保一切准备就绪！

```bash
# 发布到 PyPI
make publish

# 或使用脚本
./scripts/publish.sh pypi
```

发布成功后，可以通过以下方式安装:

```bash
# 使用传统 pip
pip install langchain-agent

# 或使用 uv (推荐)
uv pip install langchain-agent
```

## 📌 版本管理

### 语义化版本

遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/) 规范:

- **MAJOR（主版本号）**: 不兼容的 API 修改
- **MINOR（次版本号）**: 向下兼容的功能性新增
- **PATCH（修订号）**: 向下兼容的问题修正

示例:
- `0.1.0` → `0.2.0`: 添加新功能
- `0.2.0` → `0.2.1`: 修复 bug
- `0.2.1` → `1.0.0`: 重大更新，可能不兼容

### 创建 Git 标签

```bash
# 创建版本标签
git tag -a v0.1.0 -m "Release version 0.1.0"

# 推送标签到远程
git push origin v0.1.0

# 或推送所有标签
git push --tags
```

### 版本号管理最佳实践

1. **开发版本**: `0.x.x` (未稳定版本)
2. **稳定版本**: `1.0.0+` (API 稳定)
3. **预发布版本**: `1.0.0-alpha.1`, `1.0.0-beta.2`, `1.0.0-rc.1`

## 🔍 故障排除

### 构建失败

**问题**: `ModuleNotFoundError: No module named 'build'`

**解决**:
```bash
# 使用 uv
uv pip install --upgrade build

# 或使用 pip
pip install --upgrade build
```

### 上传失败

**问题**: `403 Forbidden` 或认证失败

**解决**:
1. 检查 `~/.pypirc` 配置是否正确
2. 确认 API token 有效
3. 检查用户名是否为 `__token__`

**问题**: `400 Bad Request: File already exists`

**解决**:
- PyPI 不允许重新上传相同版本
- 增加版本号后重新构建和上传

### 导入失败

**问题**: 安装后无法导入模块

**解决**:
1. 检查 `pyproject.toml` 中的 `packages` 配置
2. 确认 `src/` 目录结构正确
3. 检查 `MANIFEST.in` 是否包含必要文件

### 依赖问题

**问题**: 安装时依赖冲突

**解决**:
1. 检查 `pyproject.toml` 中的依赖版本范围
2. 使用虚拟环境测试
3. 更新 `requirements.txt`

### pyenv 版本问题

**问题**: `pyenv: version 'X.X' is not installed`

**原因**: 项目的 `.python-version` 文件指定的 Python 版本在你的系统中未安装。

**解决方案**:

```bash
# 方案1: 使用 uv pip (推荐,不受 pyenv 影响)
uv pip install langchain-agent

# 方案2: 安装指定的 Python 版本
pyenv install 3.10  # 项目要求 Python >= 3.10

# 方案3: 修改 .python-version 为已安装的版本
pyenv versions  # 先查看已安装的版本
echo "3.11" > .python-version  # 改为你已有的版本
```

**说明**:
- 本项目同时支持 `uv` 和传统 `pip`
- 使用 `uv pip` 可以避免 pyenv 版本冲突
- 项目要求 Python >= 3.10,支持 3.10、3.11、3.12 (因 langchain 依赖要求)

## 📚 相关文档

- [PyPI 官方文档](https://packaging.python.org/)
- [PEP 517 - 构建系统接口](https://www.python.org/dev/peps/pep-0517/)
- [PEP 518 - pyproject.toml](https://www.python.org/dev/peps/pep-0518/)
- [Hatchling 文档](https://hatch.pypa.io/latest/)
- [Twine 文档](https://twine.readthedocs.io/)

## 🔗 快速命令参考

```bash
# 开发
make install-dev          # 安装开发依赖
make install-local        # 安装本地开发版本
make test                 # 运行测试
make format               # 格式化代码
make lint                 # 代码检查

# 构建
make clean-build          # 清理构建文件
make build                # 构建包
make build-check          # 检查包有效性

# 发布
make check-version        # 检查版本信息
make pre-release          # 发布前完整检查
make publish-test         # 发布到 TestPyPI
make publish              # 发布到 PyPI

# 清理
make clean                # 清理临时文件
make clean-build          # 清理构建文件
```

## 📝 发布流程示例

完整的发布流程:

```bash
# 1. 更新代码和版本
# 编辑 pyproject.toml 更新版本号
# 编辑 CHANGELOG.md 记录更改

# 2. 提交更改
git add .
git commit -m "Bump version to 0.2.0"

# 3. 运行发布前检查
make pre-release

# 4. 测试发布到 TestPyPI
make publish-test

# 5. 测试安装
pip install -i https://test.pypi.org/simple/ langchain-agent  # 或使用 uv pip
langchain-chat  # 测试功能

# 6. 正式发布到 PyPI
make publish

# 7. 创建版本标签
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin master
git push --tags

# 8. 验证安装
pip install langchain-agent --upgrade  # 或使用 uv pip
```

---

**注意**: 
- 发布到 PyPI 是**永久性**的，无法删除已发布的版本
- 建议先在 TestPyPI 上测试
- 确保所有测试通过再发布
- 保持版本号的一致性和规范性

