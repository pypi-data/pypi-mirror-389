#!/bin/bash
# 版本检查脚本
# 用于检查版本号一致性和发布前的准备工作

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔍 检查项目版本信息..."

# 从 pyproject.toml 读取版本
VERSION=$(grep -E "^version = " pyproject.toml | cut -d'"' -f2)
echo -e "${GREEN}📌 当前版本: ${VERSION}${NC}"

# 检查 CHANGELOG.md 是否更新
if grep -q "## \[${VERSION}\]" CHANGELOG.md; then
    echo -e "${GREEN}✅ CHANGELOG.md 已更新版本 ${VERSION}${NC}"
else
    echo -e "${YELLOW}⚠️  CHANGELOG.md 中未找到版本 ${VERSION} 的更新记录${NC}"
    echo "💡 请在 CHANGELOG.md 中添加版本 ${VERSION} 的更新日志"
fi

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  有未提交的更改:${NC}"
    git status --short
    echo ""
    echo "💡 建议在发布前提交所有更改"
else
    echo -e "${GREEN}✅ 工作目录干净，无未提交更改${NC}"
fi

# 检查是否有版本标签
if git tag | grep -q "^v${VERSION}$"; then
    echo -e "${YELLOW}⚠️  标签 v${VERSION} 已存在${NC}"
else
    echo -e "${GREEN}✅ 标签 v${VERSION} 尚未创建${NC}"
    echo "💡 发布前可以创建标签: git tag -a v${VERSION} -m 'Release ${VERSION}'"
fi

# 检查远程分支状态
REMOTE_DIFF=$(git rev-list HEAD...origin/$(git branch --show-current) --count 2>/dev/null || echo "0")
if [ "$REMOTE_DIFF" != "0" ]; then
    echo -e "${YELLOW}⚠️  本地分支与远程分支不同步${NC}"
    echo "💡 建议运行: git push origin $(git branch --show-current)"
else
    echo -e "${GREEN}✅ 本地与远程分支已同步${NC}"
fi

echo ""
echo -e "${GREEN}✅ 版本检查完成${NC}"
echo ""
echo "📋 发布前检查清单:"
echo "  [ ] 更新 CHANGELOG.md"
echo "  [ ] 提交所有代码更改"
echo "  [ ] 运行测试 (make test)"
echo "  [ ] 构建包 (make build)"
echo "  [ ] 创建版本标签 (git tag -a v${VERSION} -m 'Release ${VERSION}')"
echo "  [ ] 推送到远程仓库 (git push && git push --tags)"
echo "  [ ] 发布到 PyPI (make publish)"

