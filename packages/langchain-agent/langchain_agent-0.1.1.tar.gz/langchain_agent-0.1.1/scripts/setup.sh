#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     LangChain Agent 项目设置脚本                        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查 Python 版本
echo -e "${YELLOW}检查 Python 版本...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}错误: 未找到 Python 3${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓ Python 版本: $PYTHON_VERSION${NC}"

# 检查是否有 uv
if command -v uv &> /dev/null; then
    echo -e "${GREEN}✓ 找到 uv 包管理器${NC}"
    echo -e "${YELLOW}安装依赖...${NC}"
    uv sync
    
    echo -e "${YELLOW}是否安装开发依赖? (y/n)${NC}"
    read -r install_dev
    if [[ $install_dev == "y" ]]; then
        uv sync --extra dev
        echo -e "${GREEN}✓ 开发依赖安装完成${NC}"
    fi
else
    echo -e "${YELLOW}未找到 uv，使用 pip 安装...${NC}"
    
    # 创建虚拟环境
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}创建虚拟环境...${NC}"
        python3 -m venv .venv
        echo -e "${GREEN}✓ 虚拟环境创建完成${NC}"
    fi
    
    # 激活虚拟环境
    source .venv/bin/activate
    
    # 升级 pip
    pip install --upgrade pip
    
    # 安装依赖
    pip install -r requirements.txt
    echo -e "${GREEN}✓ 依赖安装完成${NC}"
fi

# 创建 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}创建 .env 文件...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env 文件创建完成${NC}"
    echo -e "${YELLOW}请编辑 .env 文件配置您的环境变量${NC}"
else
    echo -e "${GREEN}✓ .env 文件已存在${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              设置完成！                                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}下一步：${NC}"
echo -e "  1. 编辑 .env 文件（如需要）"
echo -e "  2. 运行应用: ${YELLOW}make run${NC}"
echo -e "  3. 运行测试: ${YELLOW}make test${NC} 或 ${YELLOW}./scripts/run_tests.sh${NC}"
echo ""
echo -e "${BLUE}更多信息请查看 README.md${NC}"

