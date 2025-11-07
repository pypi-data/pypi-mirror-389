# 快速开始指南

## 🚀 5 分钟快速上手

### 前置要求

- Python 3.10+
- Ollama（运行本地 LLM）

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd langchain_agent
```

### 2. 自动设置（推荐）

运行设置脚本：

```bash
./scripts/setup.sh
```

这个脚本会：
- 检查 Python 版本
- 安装依赖
- 创建 .env 配置文件

### 3. 手动设置（备选）

#### 使用 uv

```bash
# 安装依赖
uv sync

# 安装开发依赖（可选）
uv sync --extra dev
```

#### 使用 pip

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置（可选）

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
vim .env  # 或使用你喜欢的编辑器
```

### 5. 运行应用

```bash
# 直接运行
python main.py

# 或使用 Makefile
make run
```

## 💡 基本使用

### 开始对话

```
😊 You: Hello!
🤖 AI: Hello! How can I help you today?
```

### 查询时间

```
😊 You: What's the current time in Tokyo?
🤖 AI: The current time in Tokyo (Asia/Tokyo) is 15:30:45.
```

### 使用命令

- 输入 `help` 查看帮助
- 输入 `clear` 清空屏幕
- 输入 `quit` 或 `exit` 退出

## 🧪 运行测试

```bash
# 运行所有测试
make test

# 或使用脚本
./scripts/run_tests.sh

# 生成覆盖率报告
make coverage
```

## 🔧 开发

### 代码格式化

```bash
make format
```

### 代码检查

```bash
make lint
```

### 清理临时文件

```bash
make clean
```

## 🐳 使用 Docker

### 构建镜像

```bash
docker build -t langchain-agent .
```

### 运行容器

```bash
docker-compose up
```

## 📚 更多资源

- [完整文档](README.md)
- [项目架构](ARCHITECTURE.md)
- [贡献指南](CONTRIBUTING.md)
- [更新日志](CHANGELOG.md)

## ❓ 常见问题

### Q: 提示找不到模块？

**A:** 确保已激活虚拟环境并安装了依赖：
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Q: Ollama 连接失败？

**A:** 确保 Ollama 服务正在运行：
```bash
# 检查 Ollama 状态
ollama list

# 启动 Ollama（如需要）
ollama serve
```

### Q: 如何添加新工具？

**A:** 在 `tools.py` 中添加：
```python
@tool
def your_tool(param: str) -> str:
    """工具描述"""
    return result

def get_all_tools():
    return [get_current_time, your_tool]
```

### Q: 如何修改 LLM 模型？

**A:** 编辑 `.env` 文件：
```
LLM_MODEL=your-model-name
```

或直接修改 `config.py` 中的默认值。

## 🆘 获取帮助

- 查看 [Issues](../../issues)
- 阅读 [文档](README.md)
- 提交新 Issue

## 🎉 开始使用

现在你已经准备好了！运行 `python main.py` 开始与 AI 对话吧！

祝你使用愉快！🚀

