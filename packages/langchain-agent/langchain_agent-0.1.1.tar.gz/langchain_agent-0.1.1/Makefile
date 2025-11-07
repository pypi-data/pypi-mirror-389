.PHONY: help install install-dev run test coverage format lint clean build build-check install-local publish publish-test check-version bump-version

help:  ## 显示帮助信息
	@echo "可用命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## 安装依赖
	uv sync

install-dev:  ## 安装开发依赖
	uv sync --extra dev

run:  ## 运行应用
	uv run python main.py

test:  ## 运行测试
	uv run --extra dev pytest

coverage:  ## 生成测试覆盖率报告
	uv run --extra dev pytest --cov=. --cov-report=html --cov-report=term

format:  ## 格式化代码
	uv run --extra dev black src/ tests/ main.py

lint:  ## 代码检查
	uv run --extra dev flake8 src/ tests/ main.py
	uv run --extra dev mypy src/

clean:  ## 清理临时文件
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean-build:  ## 清理构建文件
	rm -rf build/ dist/ *.egg-info src/*.egg-info

build:  ## 构建项目包
	@bash scripts/build.sh

build-check:  ## 检查构建的包
	@if [ ! -d "dist" ] || [ -z "$$(ls -A dist 2>/dev/null)" ]; then \
		echo "❌ dist 目录不存在或为空，请先运行 make build"; \
		exit 1; \
	fi
	@echo "🔍 检查包的有效性..."
	@uv pip install twine 2>/dev/null || pip install twine
	@twine check dist/*

install-local:  ## 安装本地开发版本
	uv pip install -e .

install-from-build:  ## 从构建包安装
	@if [ ! -d "dist" ] || [ -z "$$(ls -A dist/*.whl 2>/dev/null)" ]; then \
		echo "❌ 未找到 wheel 包，请先运行 make build"; \
		exit 1; \
	fi
	uv pip install dist/*.whl --force-reinstall

publish-test:  ## 发布到 TestPyPI
	@bash scripts/publish.sh testpypi

publish:  ## 发布到 PyPI
	@bash scripts/publish.sh pypi

check-version:  ## 检查版本信息
	@bash scripts/check_version.sh

bump-version:  ## 更新版本号
	@bash scripts/bump_version.sh

pre-release: clean-build test check-version build build-check  ## 发布前的完整检查

.DEFAULT_GOAL := help

