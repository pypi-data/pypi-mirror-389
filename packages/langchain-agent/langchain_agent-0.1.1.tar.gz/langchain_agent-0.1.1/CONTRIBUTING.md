# 贡献指南

感谢您对本项目的关注！我们欢迎任何形式的贡献。

## 🚀 开始贡献

### 1. Fork 项目

点击 GitHub 页面右上角的 "Fork" 按钮，创建项目的副本。

### 2. 克隆仓库

```bash
git clone https://github.com/your-username/langchain-example.git
cd langchain-example
```

### 3. 创建分支

```bash
git checkout -b feature/your-feature-name
```

分支命名规范：
- `feature/` - 新功能
- `bugfix/` - Bug 修复
- `docs/` - 文档更新
- `refactor/` - 代码重构
- `test/` - 测试相关

### 4. 设置开发环境

```bash
# 安装开发依赖
make install-dev

# 或使用 uv
uv sync --extra dev
```

## 📝 开发规范

### 代码风格

我们使用以下工具来保持代码质量：

- **Black** - 代码格式化
- **Flake8** - 代码检查
- **MyPy** - 类型检查

在提交前，请运行：

```bash
# 格式化代码
make format

# 代码检查
make lint
```

### 提交信息规范

使用清晰、描述性的提交信息：

```
类型: 简短描述（不超过 50 字符）

详细描述（如需要）
- 改动点 1
- 改动点 2

相关 Issue: #123
```

类型标签：
- `feat:` - 新功能
- `fix:` - Bug 修复
- `docs:` - 文档更新
- `style:` - 代码格式（不影响功能）
- `refactor:` - 重构
- `test:` - 测试相关
- `chore:` - 构建/工具相关

示例：
```
feat: 添加天气查询工具

- 实现 get_weather() 函数
- 添加相关测试
- 更新文档

相关 Issue: #42
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
make test

# 生成覆盖率报告
make coverage
```

### 编写测试

- 所有新功能都应该有对应的测试
- 测试文件放在 `tests/` 目录下
- 测试文件命名为 `test_*.py`
- 测试函数命名为 `test_*`

示例：

```python
def test_your_function():
    """测试函数的描述"""
    result = your_function("input")
    assert result == "expected_output"
```

## 📚 文档

### 代码注释

- 使用 docstring 为函数和类添加文档
- 遵循 Google 风格的 docstring

```python
def your_function(param1: str, param2: int) -> str:
    """
    函数的简短描述
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
    
    Returns:
        返回值的描述
    
    Raises:
        ValueError: 什么情况下抛出此异常
    """
    pass
```

### 更新文档

如果您的更改影响到用户使用方式，请更新 `README.md`。

## 🔄 提交 Pull Request

### 1. 推送更改

```bash
git add .
git commit -m "feat: 添加新功能"
git push origin feature/your-feature-name
```

### 2. 创建 Pull Request

在 GitHub 上创建 Pull Request，并：

1. 使用清晰的标题描述更改
2. 在描述中说明：
   - 更改的内容
   - 为什么需要这个更改
   - 如何测试
   - 相关的 Issue 编号
3. 确保所有测试通过
4. 确保代码通过 lint 检查

### 3. 代码审查

- 回应审查者的评论
- 根据反馈进行修改
- 保持耐心和礼貌

## 🐛 报告 Bug

如果您发现 Bug，请：

1. 检查是否已有相关 Issue
2. 如果没有，创建新 Issue
3. 提供以下信息：
   - 清晰的标题
   - 详细的问题描述
   - 复现步骤
   - 期望的行为
   - 实际的行为
   - 环境信息（Python 版本、操作系统等）
   - 相关的错误信息和日志

## 💡 提出新功能

如果您有新功能的想法：

1. 创建 Issue 讨论
2. 说明功能的用途和价值
3. 如果可能，提供设计方案
4. 等待维护者的反馈

## ❓ 需要帮助？

- 查看 [README.md](README.md)
- 查看现有的 Issues
- 创建新 Issue 提问

## 📜 许可证

通过贡献代码，您同意您的贡献将在 MIT 许可证下发布。

## 🙏 感谢

感谢所有贡献者的付出！

