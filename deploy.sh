#!/bin/bash
# ================================================================
# 金宫味业 - 腾讯云一键部署脚本
# 适用: 腾讯云轻量应用服务器 / CVM (Ubuntu 22.04 / CentOS 7)
# 使用前: chmod +x deploy.sh && ./deploy.sh
# AI生成: 脚本基础骨架
# 人工修改: 腾讯云镜像加速、防火墙配置、定时巡检
# ================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  金宫味业数字营销数据中台 部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# ----------------------------------------------
# 1. 环境检查
# ----------------------------------------------
echo -e "${YELLOW}[1/5] 检查环境...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker 未安装，正在安装...${NC}"
    curl -fsSL https://get.docker.com | bash
    systemctl enable docker && systemctl start docker
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose 未安装，正在安装...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo -e "${GREEN}Docker $(docker --version)${NC}"
echo -e "${GREEN}Compose $(docker-compose --version)${NC}"

# ----------------------------------------------
# 2. 配置环境变量
# ----------------------------------------------
echo -e "${YELLOW}[2/5] 配置环境变量...${NC}"

if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}已创建 .env 文件，请修改其中的密钥配置${NC}"
    echo -e "${YELLOW}  vim .env   # 修改 DEEPSEEK_API_KEY 等${NC}"
    read -p "配置完成后按回车继续..."
fi

# ----------------------------------------------
# 3. 防火墙配置 (腾讯云安全组)
# ----------------------------------------------
echo -e "${YELLOW}[3/5] 配置防火墙...${NC}"

# 检查腾讯云安全组是否已开放端口 (需在腾讯云控制台操作)
echo -e "${YELLOW}请确保腾讯云安全组已开放以下端口:${NC}"
echo -e "  80 (HTTP)"
echo -e "  443 (HTTPS)"
echo -e "  8000 (API 直连 - 开发调试用)"
echo -e ""

if command -v ufw &> /dev/null; then
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8000/tcp
    echo -e "${GREEN}防火墙已配置${NC}"
fi

# ----------------------------------------------
# 4. 构建并启动服务
# ----------------------------------------------
echo -e "${YELLOW}[4/5] 构建 Docker 镜像并启动服务...${NC}"

# 使用腾讯云 Docker 镜像加速
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
systemctl restart docker

docker-compose pull 2>/dev/null || true
docker-compose build --no-cache
docker-compose up -d

echo -e "${GREEN}服务已启动${NC}"

# ----------------------------------------------
# 5. 健康检查
# ----------------------------------------------
echo -e "${YELLOW}[5/5] 健康检查...${NC}"
sleep 5

# 检查后端
if curl -sf http://localhost:8000/ > /dev/null; then
    echo -e "${GREEN}✅ 后端 API 正常${NC}"
else
    echo -e "${RED}❌ 后端 API 异常，请检查日志: docker-compose logs backend${NC}"
fi

# 检查 MySQL
if docker-compose exec -T mysql mysqladmin ping -h localhost 2>/dev/null; then
    echo -e "${GREEN}✅ MySQL 正常${NC}"
else
    echo -e "${YELLOW}⚠️  MySQL 可能尚未就绪，等待10秒后重试${NC}"
fi

# 检查 Redis
if docker-compose exec -T redis redis-cli -a "${REDIS_PASSWORD:-JingongRedis2026!}" ping 2>/dev/null | grep -q PONG; then
    echo -e "${GREEN}✅ Redis 正常${NC}"
else
    echo -e "${YELLOW}⚠️  Redis 可能尚未就绪${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}  API 地址: http://你的服务器IP:8000${NC}"
echo -e "${GREEN}  查看日志: docker-compose logs -f backend${NC}"
echo -e "${GREEN}  停止服务: docker-compose down${NC}"
echo -e "${GREEN}========================================${NC}"

# 定时巡检脚本 (可选)
cat > /opt/jingong-health-check.sh <<'HEALTHCHECK'
#!/bin/bash
# 每5分钟执行一次健康检查，异常自动重启
STATUS=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ "$STATUS" != "200" ]; then
    echo "$(date): 后端异常 (HTTP $STATUS)，自动重启中..." >> /var/log/jingong-monitor.log
    cd /opt/jingong-marketing && docker-compose restart backend
fi
HEALTHCHECK
chmod +x /opt/jingong-health-check.sh

echo -e "${YELLOW}健康巡检脚本已生成: /opt/jingong-health-check.sh${NC}"
echo -e "${YELLOW}建议添加到 crontab: */5 * * * * /opt/jingong-health-check.sh${NC}"
