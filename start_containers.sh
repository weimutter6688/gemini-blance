#!/bin/bash

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}开始容器化部署...${NC}"

# 停止并移除现有容器（如果存在）
echo -e "${YELLOW}停止并移除现有容器...${NC}"
docker-compose down

# 构建并启动容器
echo -e "${YELLOW}构建并启动容器...${NC}"
docker-compose up -d --build

# 等待容器启动完成
echo -e "${YELLOW}等待容器启动完成...${NC}"
echo -e "${YELLOW}MySQL容器可能需要一些时间来初始化...${NC}"
sleep 10

# 检查容器状态
echo -e "${YELLOW}检查容器状态...${NC}"
if [ "$(docker ps -q -f name=gemini-balance)" ]; then
    echo -e "${GREEN}gemini-balance容器正在运行${NC}"
else
    echo -e "${RED}gemini-balance容器未运行${NC}"
    docker-compose logs gemini-balance
    exit 1
fi

if [ "$(docker ps -q -f name=gemini-balance-mysql)" ]; then
    echo -e "${GREEN}MySQL容器正在运行${NC}"
else
    echo -e "${RED}MySQL容器未运行${NC}"
    docker-compose logs mysql
    exit 1
fi

# 等待应用程序启动完成
echo -e "${YELLOW}等待应用程序启动完成...${NC}"
echo -e "${YELLOW}这可能需要一些时间...${NC}"
sleep 20

# 验证应用程序是否正常运行
echo -e "${YELLOW}验证应用程序是否正常运行...${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$response" == "200" ]; then
    echo -e "${GREEN}应用程序正常运行！${NC}"
    echo -e "${GREEN}您可以通过访问 http://localhost:8000 来使用应用程序${NC}"
else
    echo -e "${RED}应用程序未正常运行，HTTP状态码: $response${NC}"
    echo -e "${YELLOW}查看容器日志以获取更多信息...${NC}"
    docker-compose logs gemini-balance
fi

# 测试代理配置
echo -e "${YELLOW}测试代理配置...${NC}"
echo -e "${YELLOW}这将运行三种不同的测试方法：${NC}"
echo -e "${YELLOW}1. 使用硬编码的代理地址${NC}"
echo -e "${YELLOW}2. 使用环境变量中的代理配置${NC}"
echo -e "${YELLOW}3. 使用与应用程序完全相同的方式创建和使用代理配置${NC}"
docker-compose exec gemini-balance python /app/test_proxy_in_container.py

# 打印应用程序日志
echo -e "${YELLOW}应用程序日志：${NC}"
docker-compose logs --tail=50 gemini-balance

echo -e "${YELLOW}容器日志：${NC}"
docker-compose logs --tail=20 gemini-balance

echo -e "${YELLOW}部署完成${NC}"