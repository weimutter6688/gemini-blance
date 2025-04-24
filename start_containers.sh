#!/bin/bash

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 设置错误处理
set -e  # 遇到错误时立即退出
trap 'echo -e "${RED}脚本执行失败${NC}"; exit 1' ERR

# 函数：执行命令并检查结果
execute_command() {
    echo -e "${YELLOW}执行: $1${NC}"
    eval "$1"
    if [ $? -ne 0 ]; then
        echo -e "${RED}命令执行失败: $1${NC}"
        return 1
    fi
    return 0
}

echo -e "${YELLOW}开始容器化部署...${NC}"

# 停止并移除现有容器（如果存在）
echo -e "${YELLOW}停止并移除现有容器...${NC}"
if ! execute_command "docker-compose down"; then
    echo -e "${RED}无法停止现有容器，退出部署${NC}"
    exit 1
fi

# 构建并启动容器
echo -e "${YELLOW}构建并启动容器...${NC}"
if ! execute_command "docker-compose up -d --build"; then
    echo -e "${RED}无法构建和启动容器，退出部署${NC}"
    exit 1
fi

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
sleep 60

# 验证应用程序是否正常运行
echo -e "${YELLOW}验证应用程序是否正常运行...${NC}"
MAX_RETRIES=3
RETRY_COUNT=0
APP_RUNNING=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
    
    if [ "$response" == "200" ]; then
        echo -e "${GREEN}应用程序正常运行！${NC}"
        echo -e "${GREEN}您可以通过访问 http://localhost:8000 来使用应用程序${NC}"
        APP_RUNNING=true
        break
    else
        RETRY_COUNT=$((RETRY_COUNT+1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo -e "${YELLOW}应用程序未正常运行，HTTP状态码: $response，等待10秒后重试 ($RETRY_COUNT/$MAX_RETRIES)...${NC}"
            sleep 10
        else
            echo -e "${RED}应用程序未正常运行，HTTP状态码: $response，已达到最大重试次数${NC}"
            echo -e "${YELLOW}查看容器日志以获取更多信息...${NC}"
            docker-compose logs gemini-balance
            
            # 询问用户是否继续
            read -p "应用程序未正常运行，是否继续执行脚本？(y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${RED}用户选择退出${NC}"
                exit 1
            fi
        fi
    fi
done

# 测试代理配置
echo -e "${YELLOW}测试代理配置...${NC}"
echo -e "${YELLOW}这将运行三种不同的测试方法：${NC}"
echo -e "${YELLOW}1. 使用从.env文件读取的代理地址${NC}"
echo -e "${YELLOW}2. 使用环境变量中的代理配置${NC}"
echo -e "${YELLOW}3. 使用与应用程序完全相同的方式创建和使用代理配置${NC}"

if ! execute_command "docker-compose exec -T gemini-balance python /app/test_proxy_in_container.py"; then
    echo -e "${RED}代理测试失败${NC}"
    
    # 询问用户是否继续
    read -p "代理测试失败，是否继续执行脚本？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}用户选择退出${NC}"
        exit 1
    fi
fi

# 打印应用程序日志
echo -e "${YELLOW}应用程序日志：${NC}"
execute_command "docker-compose logs --tail=50 gemini-balance" || true

echo -e "${YELLOW}容器日志：${NC}"
execute_command "docker-compose logs --tail=20 gemini-balance" || true

echo -e "${GREEN}部署完成${NC}"