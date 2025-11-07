#!/bin/bash
# 项目打包脚本
# 用于构建 Python 包的 wheel 和 sdist 发行版

set -e  # 遇到错误立即退出

echo "🚀 开始构建 langchain_agent 项目..."

# 清理旧的构建文件
echo "🧹 清理旧的构建文件..."
rm -rf build/ dist/ *.egg-info src/*.egg-info

# 检查是否安装了 build 工具
if ! command -v uv &> /dev/null; then
    echo "⚠️  未安装 uv，使用 pip 安装 build..."
    python -m pip install --upgrade build
    BUILD_CMD="python -m build"
else
    echo "✅ 使用 uv 构建..."
    # 确保安装了 build 工具
    uv pip install --upgrade build
    BUILD_CMD="uv run python -m build"
fi

# 构建项目
echo "📦 构建 wheel 和 sdist..."
$BUILD_CMD

# 检查构建结果
if [ -d "dist" ] && [ "$(ls -A dist)" ]; then
    echo ""
    echo "✅ 构建成功！"
    echo "📦 生成的包文件："
    ls -lh dist/
    echo ""
    echo "💡 提示："
    echo "  - 使用 'pip install dist/langchain_agent-*.whl' 进行本地安装"
    echo "  - 使用 'twine upload dist/*' 上传到 PyPI"
    echo "  - 使用 'make install-local' 安装本地开发版本"
else
    echo "❌ 构建失败，未找到 dist 目录或目录为空"
    exit 1
fi

