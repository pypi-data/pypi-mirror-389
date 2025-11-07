#!/bin/bash
# 项目发布脚本
# 用于将项目发布到 PyPI 或 TestPyPI

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 默认发布到 TestPyPI
REPOSITORY=${1:-testpypi}

echo "📦 准备发布 langchain_agent 到 ${REPOSITORY}..."

# 检查是否安装了 twine
if ! command -v twine &> /dev/null; then
    echo -e "${YELLOW}⚠️  未安装 twine，正在安装...${NC}"
    pip install --upgrade twine
fi

# 检查 dist 目录
if [ ! -d "dist" ] || [ -z "$(ls -A dist 2>/dev/null)" ]; then
    echo -e "${RED}❌ dist 目录不存在或为空，请先运行构建脚本${NC}"
    echo "💡 运行: make build 或 ./scripts/build.sh"
    exit 1
fi

# 显示将要上传的文件
echo ""
echo "📦 将要上传的文件："
ls -lh dist/
echo ""

# 检查包的有效性
echo "🔍 检查包的有效性..."
twine check dist/*

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 包检查失败，请修复错误后重试${NC}"
    exit 1
fi

# 确认发布
read -p "❓ 确认要发布到 ${REPOSITORY} 吗? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 取消发布"
    exit 0
fi

# 根据仓库选择上传
if [ "$REPOSITORY" == "pypi" ]; then
    echo "🚀 上传到 PyPI..."
    twine upload dist/*
elif [ "$REPOSITORY" == "testpypi" ]; then
    echo "🚀 上传到 TestPyPI..."
    twine upload --repository testpypi dist/*
else
    echo -e "${RED}❌ 未知的仓库: ${REPOSITORY}${NC}"
    echo "💡 使用方法: $0 [pypi|testpypi]"
    exit 1
fi

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 发布成功！${NC}"
    if [ "$REPOSITORY" == "testpypi" ]; then
        echo "🔗 TestPyPI: https://test.pypi.org/project/langchain-agent/"
        echo "💡 测试安装: pip install -i https://test.pypi.org/simple/ langchain-agent"
    else
        echo "🔗 PyPI: https://pypi.org/project/langchain-agent/"
        echo "💡 安装命令: pip install langchain-agent"
    fi
else
    echo -e "${RED}❌ 发布失败${NC}"
    exit 1
fi

