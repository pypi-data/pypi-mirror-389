# 项目架构文档

## 📐 整体架构

本项目采用模块化设计，将不同的功能职责分离到独立的模块中。

```
┌─────────────────────────────────────────────────┐
│                   main.py                        │
│            (应用入口 & 主循环)                    │
└────────────┬────────────────────────────────────┘
             │
             ├─────────────────┐
             │                 │
             ▼                 ▼
    ┌────────────────┐  ┌──────────────┐
    │   config.py    │  │   utils.py   │
    │   (配置管理)    │  │  (工具函数)   │
    └────────┬───────┘  └──────────────┘
             │
             ▼
    ┌────────────────┐
    │    agent.py    │
    │  (Agent封装)   │
    └────────┬───────┘
             │
             ├─────────────────┐
             │                 │
             ▼                 ▼
    ┌────────────────┐  ┌──────────────┐
    │   tools.py     │  │ LangChain    │
    │  (工具定义)     │  │   Ollama     │
    └────────────────┘  └──────────────┘
```

## 🔧 模块说明

### 0. main.py - 应用入口点

**职责：**
- 作为应用的启动入口
- 导入并调用核心主函数

**说明：**
这是一个简单的入口文件，将实际的应用逻辑委托给 `src/langchain_agent/main.py`。

### 1. src/langchain_agent/main.py - 主程序逻辑

**职责：**
- 应用初始化
- 主循环管理
- 用户交互处理
- 异常捕获

**关键函数：**
- `main()` - 应用入口点
- `run_chat_loop()` - 聊天循环

**设计模式：**
- 命令模式（处理用户命令）
- 外观模式（简化子系统接口）

### 2. config.py - 配置管理

**职责：**
- 集中管理配置
- 环境变量加载
- 配置验证

**主要类：**
- `LLMConfig` - LLM 相关配置
- `AgentConfig` - Agent 相关配置
- `AppConfig` - 应用总配置

**设计模式：**
- 数据类模式（使用 @dataclass）
- 工厂模式（from_env 方法）

**优点：**
- 配置集中管理
- 易于扩展
- 类型安全
- 支持默认值

### 3. agent.py - Agent 封装

**职责：**
- 封装 LLM 和 Agent 的创建
- 提供简洁的对话接口
- 错误处理和日志记录

**主要类：**
- `ChatAgent` - 聊天代理封装类

**关键方法：**
- `__init__()` - 初始化
- `_create_llm()` - 创建 LLM 实例
- `_create_agent()` - 创建 Agent 实例
- `chat()` - 处理对话
- `get_model_info()` - 获取模型信息

**设计模式：**
- 外观模式（简化 LangChain API）
- 单例模式（一个应用实例一个 Agent）

**优点：**
- 隐藏 LangChain 的复杂性
- 易于测试和维护
- 清晰的职责划分

### 4. src/langchain_agent/tools.py - 工具定义

**职责：**
- 定义 Agent 可用的工具
- 工具功能实现
- 工具注册和管理

**主要函数：**
- `get_current_time()` - 时区查询工具
- `get_all_tools()` - 返回所有可用工具

**设计模式：**
- 装饰器模式（@tool 装饰器）
- 注册模式（get_all_tools）

**扩展性：**
```python
# 添加新工具只需：
@tool
def new_tool(param: str) -> str:
    """工具描述"""
    return result

# 然后在 get_all_tools() 中注册
def get_all_tools():
    return [get_current_time, new_tool]
```

### 5. utils.py - 通用工具

**职责：**
- 日志配置
- 界面美化
- 通用辅助函数

**主要函数：**
- `setup_logging()` - 配置日志系统
- `print_welcome()` - 打印欢迎信息
- `print_help()` - 打印帮助信息
- `clear_screen()` - 清空屏幕

## 🔄 数据流

### 用户输入 → AI 回复的完整流程

```
1. 用户输入
   ↓
2. main.py 接收输入
   ↓
3. ChatAgent.chat() 处理
   ↓
4. LangChain Agent 分析
   ↓
5. 决定是否需要使用工具
   ├─ 需要工具
   │  ↓
   │  调用 tools.py 中的工具
   │  ↓
   │  工具返回结果
   │  ↓
   │  LLM 基于工具结果生成回复
   │
   └─ 不需要工具
      ↓
      直接生成回复
   ↓
6. 返回最终回复
   ↓
7. main.py 显示给用户
```

## 🎯 设计原则

### 1. 单一职责原则（SRP）

每个模块只负责一个功能领域：
- `config.py` 只负责配置
- `tools.py` 只负责工具定义
- `agent.py` 只负责 Agent 封装

### 2. 开闭原则（OCP）

- 对扩展开放：可以轻松添加新工具、新配置
- 对修改关闭：添加新功能不需要修改现有代码

### 3. 依赖倒置原则（DIP）

- 高层模块（main.py）不依赖低层模块的具体实现
- 通过接口（ChatAgent 类）进行交互

### 4. 接口隔离原则（ISP）

- ChatAgent 只暴露必要的方法（chat, get_model_info）
- 隐藏内部实现细节（_create_llm, _create_agent）

## 🧪 测试架构

```
tests/
├── test_config.py      # 配置测试
├── test_tools.py       # 工具测试
└── test_agent.py       # Agent 测试（可添加）
```

### 测试策略

1. **单元测试** - 测试单个函数/方法
2. **集成测试** - 测试模块间交互
3. **端到端测试** - 测试完整流程（可选）

## 📦 依赖管理

### 核心依赖

- `langchain` - LangChain 框架
- `langchain-ollama` - Ollama 集成

### 开发依赖

- `pytest` - 测试框架
- `black` - 代码格式化
- `flake8` - 代码检查
- `mypy` - 类型检查

## 🚀 性能考虑

### 1. 懒加载

- Agent 只在需要时初始化
- 工具按需加载

### 2. 错误处理

- 每个层次都有适当的错误处理
- 不会因为单个工具失败而导致整个应用崩溃

### 3. 日志记录

- 分级日志（DEBUG, INFO, WARNING, ERROR）
- 可配置的日志输出

## 🔐 安全考虑

### 1. 环境变量

- 敏感信息（API Key）通过环境变量传递
- 不在代码中硬编码密钥

### 2. 输入验证

- 工具函数验证输入参数
- 捕获和处理异常

### 3. Docker 安全

- 使用非 root 用户运行
- 最小权限原则

## 📈 扩展性

### 添加新工具

1. 在 `src/langchain_agent/tools.py` 中定义新工具
2. 在 `get_all_tools()` 中注册
3. 在 `tests/` 中编写测试
4. 在 `src/langchain_agent/__init__.py` 中导出（可选）

### 添加新配置

1. 在相应的 Config 类中添加字段
2. 更新 `from_env()` 方法
3. 更新 `.env.example`

### 添加新命令

1. 在 `main.py` 的 `run_chat_loop()` 中添加命令处理
2. 在 `utils.py` 的 `print_help()` 中添加说明

## 🔮 未来改进方向

1. **异步支持** - 使用 asyncio 提升性能
2. **缓存机制** - 缓存常见查询结果
3. **插件系统** - 动态加载工具插件
4. **Web 界面** - 添加 Web UI
5. **多语言支持** - 国际化 (i18n)
6. **持久化** - 保存对话历史
7. **监控指标** - 添加性能监控

## 📚 参考资源

- [LangChain 文档](https://python.langchain.com/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Python 最佳实践](https://docs.python-guide.org/)

