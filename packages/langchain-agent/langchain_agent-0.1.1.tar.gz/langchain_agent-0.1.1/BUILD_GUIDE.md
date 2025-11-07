# 🚀 快速打包构建指南

本指南帮助你快速上手项目的打包和发布流程。

## ⚡ 快速开始

### 1️⃣ 构建你的第一个包

```bash
# 安装开发依赖
make install-dev

# 构建包
make build
```

构建完成后，你会在 `dist/` 目录看到:
```
dist/
├── langchain_agent-0.1.0-py3-none-any.whl
└── langchain_agent-0.1.0.tar.gz
```

### 2️⃣ 测试构建的包

```bash
# 检查包的有效性
make build-check

# 从构建的包安装
make install-from-build

# 测试运行
chat
```

### 3️⃣ 发布到 TestPyPI（测试）

```bash
# 配置 PyPI 凭据（首次需要）
cp .pypirc.example ~/.pypirc
# 编辑 ~/.pypirc 填入你的 API token

# 发布到测试服务器
make publish-test
```

### 4️⃣ 发布到正式 PyPI

```bash
# 运行发布前检查
make pre-release

# 确认无误后发布
make publish
```

## 📋 完整发布流程

### 步骤 1: 准备发布

```bash
# 1. 更新版本号
# 编辑 pyproject.toml，修改 version = "0.2.0"

# 2. 更新变更日志
# 编辑 CHANGELOG.md，添加版本更新记录

# 3. 提交更改
git add .
git commit -m "Bump version to 0.2.0"
```

### 步骤 2: 检查和构建

```bash
# 运行版本检查
make check-version

# 运行所有测试
make test

# 清理旧的构建文件
make clean-build

# 构建新包
make build
```

### 步骤 3: 测试发布

```bash
# 发布到 TestPyPI
make publish-test

# 从 TestPyPI 安装测试
pip install -i https://test.pypi.org/simple/ langchain-agent

# 测试功能
chat
```

### 步骤 4: 正式发布

```bash
# 发布到 PyPI
make publish

# 创建版本标签
git tag -a v0.2.0 -m "Release version 0.2.0"

# 推送到远程
git push origin master --tags
```

## 🔧 配置 PyPI 凭据

### 获取 API Token

1. 访问 [PyPI Account Settings](https://pypi.org/manage/account/token/)
2. 创建新的 API token
3. 复制 token（以 `pypi-` 开头）

### 配置 .pypirc

创建或编辑 `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_ACTUAL_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

**安全提示**: 不要将 `.pypirc` 提交到版本控制！

## 📦 常用命令速查

### 构建相关
```bash
make build              # 构建包
make build-check        # 检查包有效性
make clean-build        # 清理构建文件
```

### 安装相关
```bash
make install-local      # 安装本地开发版本（可编辑模式）
make install-from-build # 从构建包安装
```

### 发布相关
```bash
make check-version      # 检查版本信息
make pre-release        # 发布前完整检查
make publish-test       # 发布到 TestPyPI
make publish            # 发布到 PyPI
```

### 开发相关
```bash
make test              # 运行测试
make coverage          # 测试覆盖率
make format            # 格式化代码
make lint              # 代码检查
```

## 🎯 发布检查清单

在发布前确保:

- [ ] 更新了版本号（`pyproject.toml`）
- [ ] 更新了 CHANGELOG.md
- [ ] 所有测试通过（`make test`）
- [ ] 代码已格式化（`make format`）
- [ ] 代码检查通过（`make lint`）
- [ ] 构建成功（`make build`）
- [ ] 包检查通过（`make build-check`）
- [ ] 已在 TestPyPI 测试
- [ ] 代码已提交到 Git
- [ ] 准备创建版本标签

## 🐛 常见问题

### Q: 构建失败，提示找不到 build 模块？
```bash
# 安装 build 工具
pip install --upgrade build
```

### Q: 上传时提示 403 错误？
检查 `~/.pypirc` 配置:
- 确认 username 是 `__token__`
- 确认 password 是有效的 API token
- 确认 token 有上传权限

### Q: 上传时提示文件已存在？
PyPI 不允许重新上传相同版本:
- 增加版本号
- 重新构建
- 上传新版本

### Q: 如何撤销已发布的版本？
PyPI 不允许删除已发布的版本。建议:
- 发布一个修复版本
- 在 PyPI 上标记为 "yanked"（不推荐安装）

### Q: 测试安装时依赖安装失败？
TestPyPI 可能没有所有依赖包:
```bash
# 从 TestPyPI 安装主包，从 PyPI 安装依赖
pip install -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  langchain-agent
```

## 📚 更多资源

- [完整打包指南](PACKAGING.md) - 详细的打包说明
- [脚本使用说明](scripts/README.md) - 各脚本详细说明
- [项目文档](README.md) - 项目使用说明
- [贡献指南](CONTRIBUTING.md) - 贡献代码指南

## 💡 最佳实践

1. **版本管理**
   - 遵循语义化版本规范
   - 每次发布前更新 CHANGELOG
   - 创建版本标签

2. **测试**
   - 先在 TestPyPI 测试
   - 测试安装和功能
   - 确认所有测试通过

3. **文档**
   - 保持文档更新
   - 记录所有重要变更
   - 提供清晰的使用示例

4. **安全**
   - 不要提交 API token
   - 定期更新依赖
   - 审查代码变更

## 🎓 学习路径

1. 先学习构建基础 → `make build`
2. 本地测试安装 → `make install-from-build`
3. 发布到测试环境 → `make publish-test`
4. 最后发布到正式环境 → `make publish`

---

**需要帮助?** 查看 [PACKAGING.md](PACKAGING.md) 获取更详细的说明。

