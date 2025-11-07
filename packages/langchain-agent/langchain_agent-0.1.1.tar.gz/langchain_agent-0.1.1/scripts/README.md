# 🛠️ 脚本使用说明

本目录包含项目的各种自动化脚本。

## 📁 脚本列表

### 1. setup.sh - 项目设置脚本
自动设置项目环境。

```bash
./scripts/setup.sh
```

**功能:**
- 检查 Python 版本
- 创建虚拟环境
- 安装依赖
- 验证安装

### 2. run_tests.sh - 测试运行脚本
运行项目测试套件。

```bash
./scripts/run_tests.sh
```

**功能:**
- 运行所有单元测试
- 生成覆盖率报告
- 显示测试结果

### 3. build.sh - 打包构建脚本
构建 Python 包的发行版。

```bash
./scripts/build.sh
```

**功能:**
- 清理旧的构建文件
- 检查构建工具
- 构建 wheel 和 sdist
- 显示构建结果

**输出:**
- `dist/langchain_agent-*.whl` - wheel 包
- `dist/langchain_agent-*.tar.gz` - 源代码包

### 4. publish.sh - 发布脚本
发布包到 PyPI 或 TestPyPI。

```bash
# 发布到 TestPyPI（推荐先测试）
./scripts/publish.sh testpypi

# 发布到正式 PyPI
./scripts/publish.sh pypi
```

**功能:**
- 检查 twine 工具
- 验证包的有效性
- 上传到指定仓库
- 显示发布结果

**前置条件:**
- 需要先运行 `build.sh` 构建包
- 需要配置 `~/.pypirc` 文件

### 5. check_version.sh - 版本检查脚本
检查版本信息和发布准备状态。

```bash
./scripts/check_version.sh
```

**功能:**
- 读取当前版本号
- 检查 CHANGELOG 更新
- 检查 Git 状态
- 检查版本标签
- 显示发布检查清单

## 🚀 典型工作流

### 开发流程

```bash
# 1. 初始设置
./scripts/setup.sh

# 2. 开发代码
# ... 编写代码 ...

# 3. 运行测试
./scripts/run_tests.sh

# 4. 提交代码
git add .
git commit -m "feature: add new functionality"
```

### 发布流程

```bash
# 1. 更新版本号
# 编辑 pyproject.toml 中的 version

# 2. 更新变更日志
# 编辑 CHANGELOG.md

# 3. 检查版本信息
./scripts/check_version.sh

# 4. 运行测试
./scripts/run_tests.sh

# 5. 构建包
./scripts/build.sh

# 6. 测试发布到 TestPyPI
./scripts/publish.sh testpypi

# 7. 测试安装
pip install -i https://test.pypi.org/simple/ langchain-agent

# 8. 正式发布到 PyPI
./scripts/publish.sh pypi

# 9. 创建版本标签
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin master --tags
```

## 📝 注意事项

### 权限
所有脚本都应该有执行权限:
```bash
chmod +x scripts/*.sh
```

### 环境要求
- Python 3.10+
- uv 或 pip
- Git（用于版本管理）
- Docker（可选，用于容器化）

### 配置文件
- `.env` - 环境变量配置
- `~/.pypirc` - PyPI 认证配置

### 错误处理
所有脚本都使用 `set -e` 来确保遇到错误时立即退出。

## 🔧 Makefile 快捷方式

大部分脚本都可以通过 Makefile 命令调用:

```bash
# 相当于 ./scripts/build.sh
make build

# 相当于 ./scripts/publish.sh testpypi
make publish-test

# 相当于 ./scripts/publish.sh pypi
make publish

# 相当于 ./scripts/check_version.sh
make check-version

# 相当于 ./scripts/run_tests.sh
make test
```

使用 `make help` 查看所有可用命令。

## 📚 更多信息

- 详细的打包指南: 查看 [PACKAGING.md](../PACKAGING.md)
- 项目文档: 查看 [README.md](../README.md)
- 架构说明: 查看 [ARCHITECTURE.md](../ARCHITECTURE.md)

## 🐛 故障排除

### 脚本无法执行
```bash
# 添加执行权限
chmod +x scripts/*.sh
```

### 构建失败
```bash
# 确保安装了 build 工具
pip install --upgrade build

# 清理旧文件后重试
make clean-build
make build
```

### 发布失败
```bash
# 检查 PyPI 配置
cat ~/.pypirc

# 检查包的有效性
make build-check

# 确保版本号唯一
./scripts/check_version.sh
```

---

**提示**: 建议使用 `make` 命令而不是直接调用脚本，因为 Makefile 提供了更好的依赖管理和错误处理。

