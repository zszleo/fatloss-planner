#!/bin/bash
# 桌面模块测试脚本
# 在无头环境中运行桌面测试，支持覆盖率报告

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Fatloss Planner 桌面模块测试 ===${NC}"

# 检查是否在虚拟环境中运行
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}警告: 未检测到虚拟环境，建议在虚拟环境中运行测试${NC}"
fi

# 检查Xvfb是否安装
if ! command -v xvfb-run &> /dev/null; then
    echo -e "${RED}错误: xvfb-run 未安装。请安装Xvfb:${NC}"
    echo "  Ubuntu/Debian: sudo apt-get install xvfb"
    echo "  macOS: brew install xquartz"
    exit 1
fi

# 设置显示环境变量
export DISPLAY=:99
export QT_QPA_PLATFORM=offscreen

# 启动Xvfb后台进程
echo -e "${GREEN}启动Xvfb虚拟显示服务器...${NC}"
Xvfb :99 -screen 0 1920x1080x24 &
XVFB_PID=$!

# 确保Xvfb启动成功
sleep 2
if ! ps -p $XVFB_PID > /dev/null; then
    echo -e "${RED}错误: Xvfb启动失败${NC}"
    exit 1
fi

echo -e "${GREEN}Xvfb已启动 (PID: $XVFB_PID)${NC}"

# 清理函数
cleanup() {
    echo -e "${YELLOW}清理测试环境...${NC}"
    if ps -p $XVFB_PID > /dev/null; then
        kill $XVFB_PID 2>/dev/null || true
        echo -e "${GREEN}Xvfb已停止${NC}"
    fi
}

# 注册清理函数
trap cleanup EXIT

# 运行测试
echo -e "${GREEN}运行桌面模块测试...${NC}"
echo -e "${YELLOW}测试命令: python -m pytest tests/desktop/ -v --cov=src/fatloss/desktop --cov-report=html --cov-report=term-missing${NC}"

if python -m pytest tests/desktop/ -v \
    --cov=src/fatloss/desktop \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-fail-under=80; then
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    
    # 显示覆盖率摘要
    echo -e "${GREEN}=== 覆盖率报告 ===${NC}"
    python -m pytest tests/desktop/ --cov=src/fatloss/desktop --cov-report=term-missing --quiet
else
    echo -e "${RED}❌ 测试失败！${NC}"
    exit 1
fi

echo -e "${GREEN}=== 测试完成 ===${NC}"
echo -e "HTML覆盖率报告: file://$(pwd)/htmlcov/index.html"