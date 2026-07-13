# ================================================================
# 金宫味业数字营销数据中台 - Dockerfile
# 部署平台: 腾讯云轻量应用服务器 / 容器服务 TKE
# AI生成: 基础骨架 + 镜像优化
# 人工修改: 腾讯云专有配置、安全加固、时区设置
# ================================================================

FROM python:3.11-slim

# 维护者信息
LABEL maintainer="jingong-marketing"
LABEL description="金宫味业数字营销数据中台"

# 设置时区和编码
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 创建非root用户 (安全最佳实践)
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Debian 国内源加速
RUN sed -i 's|http://deb.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python依赖 (分层缓存优化)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.tencent.com/pypi/simple/ -r requirements.txt

# 额外依赖: MySQL驱动 + Redis客户端 (可选)
RUN pip install --no-cache-dir -i https://mirrors.tencent.com/pypi/simple/ \
    pymysql \
    cryptography \
    redis

# Playwright 及浏览器 (可选, 仅需爬虫时开启)
# RUN pip install playwright && playwright install chromium --with-deps

# 复制应用代码
COPY backend/ .

# 创建必要目录
RUN mkdir -p /app/screenshots /app/data && chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
