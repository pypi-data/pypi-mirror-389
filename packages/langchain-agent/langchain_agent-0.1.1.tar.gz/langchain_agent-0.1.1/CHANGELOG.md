# 更新日志

本文档记录项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### ✨ 新增

- 完整的项目打包配置
- 自动化构建脚本 (`scripts/build.sh`)
- PyPI 发布脚本 (`scripts/publish.sh`)
- 版本检查脚本 (`scripts/check_version.sh`)
- MANIFEST.in 文件（包含分发文件清单）
- .pypirc 配置文件模板

### 📚 文档

- 新增打包与发布指南 (PACKAGING.md)
- 新增脚本使用说明 (scripts/README.md)
- 更新 README.md 添加打包命令说明
- 更新 PROJECT_SUMMARY.md 添加打包相关内容

### 🛠️ 开发工具

- Makefile 新增打包相关命令：
  - `make build` - 构建项目包
  - `make build-check` - 检查构建的包
  - `make clean-build` - 清理构建文件
  - `make install-local` - 安装本地开发版本
  - `make install-from-build` - 从构建包安装
  - `make publish-test` - 发布到 TestPyPI
  - `make publish` - 发布到 PyPI
  - `make check-version` - 检查版本信息
  - `make pre-release` - 发布前的完整检查

### 🔧 改进

- 完善 pyproject.toml 的项目元数据
- 添加项目分类和关键词
- 配置项目 URLs（主页、仓库、问题跟踪）
- 优化构建系统配置

## [0.1.0] - 2024-11-06

### ✨ 新增

- 初始项目结构
- 基于 LangChain 的聊天代理系统
- 时区查询工具 (`get_current_time`)
- 配置管理系统（支持环境变量）
- 完整的日志系统
- 美观的命令行界面
- 交互式聊天循环
- 支持的命令：
  - `quit/exit/q` - 退出程序
  - `help` - 显示帮助
  - `clear` - 清空屏幕

### 📚 文档

- 完整的 README.md
- 项目架构文档 (ARCHITECTURE.md)
- 贡献指南 (CONTRIBUTING.md)
- MIT 许可证

### 🧪 测试

- pytest 测试框架集成
- 工具函数测试
- 配置测试
- 测试覆盖率报告

### 🛠️ 开发工具

- Makefile（常用命令快捷方式）
- Docker 支持
- docker-compose 配置
- 开发依赖（black, flake8, mypy, pytest）
- 自动化设置脚本
- 测试运行脚本

### 📦 依赖

- langchain >= 1.0.3
- langchain-ollama >= 1.0.0
- python-dotenv >= 1.0.0

## [未来计划]

### 计划添加

- [ ] 更多实用工具（天气、翻译等）
- [ ] 对话历史持久化
- [ ] Web UI 界面
- [ ] 异步处理支持
- [ ] 缓存机制
- [ ] 插件系统
- [ ] 国际化支持
- [ ] 性能监控

### 改进计划

- [ ] 更全面的测试覆盖
- [ ] 性能优化
- [ ] 更好的错误处理
- [ ] 完善的 API 文档

