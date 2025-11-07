#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 确保在项目根目录执行
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              运行测试套件                                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 运行测试
echo -e "${YELLOW}运行测试...${NC}"
make coverage

TEST_EXIT_CODE=$?

echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！${NC}"
    echo ""
    echo -e "${BLUE}测试覆盖率报告已生成到 htmlcov/index.html${NC}"
    echo -e "${BLUE}在浏览器中打开查看详细报告${NC}"
else
    echo -e "${RED}✗ 部分测试失败${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}运行代码检查...${NC}"

# 运行 lint（flake8 + mypy）
make lint
LINT_EXIT_CODE=$?

if [ $LINT_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ 代码检查通过${NC}"
else
    echo -e "${YELLOW}⚠ 代码检查发现一些问题，请查看输出${NC}"
fi

echo ""
echo -e "${GREEN}测试完成！${NC}"

