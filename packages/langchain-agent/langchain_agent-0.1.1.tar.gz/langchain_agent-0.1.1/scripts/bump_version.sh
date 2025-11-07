#!/bin/bash
# 版本号更新脚本
# 用于自动更新项目版本号

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 获取当前版本
CURRENT_VERSION=$(grep -E "^version = " pyproject.toml | cut -d'"' -f2)

echo -e "${GREEN}📌 当前版本: ${CURRENT_VERSION}${NC}"
echo ""

# 如果提供了参数，使用参数作为新版本
if [ -n "$1" ]; then
    NEW_VERSION="$1"
else
    # 否则提示用户输入
    echo "请输入新版本号（格式：X.Y.Z）:"
    echo "  - MAJOR（主版本号）: 不兼容的 API 修改"
    echo "  - MINOR（次版本号）: 向下兼容的功能性新增"
    echo "  - PATCH（修订号）: 向下兼容的问题修正"
    echo ""
    read -p "新版本号: " NEW_VERSION
fi

# 验证版本号格式
if ! [[ $NEW_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}❌ 无效的版本号格式: ${NEW_VERSION}${NC}"
    echo "版本号必须是 X.Y.Z 格式（例如：1.2.3）"
    exit 1
fi

# 检查新版本是否与当前版本相同
if [ "$NEW_VERSION" = "$CURRENT_VERSION" ]; then
    echo -e "${YELLOW}⚠️  新版本号与当前版本相同${NC}"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 取消更新"
        exit 0
    fi
fi

# 确认更新
echo ""
echo "将版本从 ${CURRENT_VERSION} 更新到 ${NEW_VERSION}"
read -p "确认更新? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 取消更新"
    exit 0
fi

# 更新 pyproject.toml
echo "📝 更新 pyproject.toml..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" pyproject.toml
else
    # Linux
    sed -i "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" pyproject.toml
fi

# 检查 CHANGELOG.md
if [ -f "CHANGELOG.md" ]; then
    if grep -q "## \[未发布\]" CHANGELOG.md; then
        echo ""
        echo -e "${YELLOW}💡 提示: 记得更新 CHANGELOG.md${NC}"
        echo "   将 [未发布] 改为 [${NEW_VERSION}] - $(date +%Y-%m-%d)"
        echo ""
        read -p "是否自动更新 CHANGELOG.md? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/## \[未发布\]/## [${NEW_VERSION}] - $(date +%Y-%m-%d)/" CHANGELOG.md
            else
                # Linux
                sed -i "s/## \[未发布\]/## [${NEW_VERSION}] - $(date +%Y-%m-%d)/" CHANGELOG.md
            fi
            echo -e "${GREEN}✅ CHANGELOG.md 已更新${NC}"
        fi
    fi
fi

echo ""
echo -e "${GREEN}✅ 版本更新成功！${NC}"
echo ""
echo "📋 下一步操作:"
echo "  1. 检查更改: git diff"
echo "  2. 测试代码: make test"
echo "  3. 提交更改: git add . && git commit -m 'Bump version to ${NEW_VERSION}'"
echo "  4. 构建项目: make build"
echo "  5. 发布项目: make publish-test（测试）或 make publish（正式）"
echo "  6. 创建标签: git tag -a v${NEW_VERSION} -m 'Release ${NEW_VERSION}'"
echo "  7. 推送标签: git push origin master --tags"

