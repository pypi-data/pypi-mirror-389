# OpenSSH同步工具Docker镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 安装项目依赖
RUN pip install --no-cache-dir -e .

# 创建下载目录
RUN mkdir -p /data/openssh

# 设置环境变量
ENV DOWNLOAD_DIR=/data/openssh
ENV CHECK_INTERVAL=24
ENV MIN_VERSION=10.2.1
ENV DEBUG=false

# 创建非root用户
RUN groupadd -r opensshsync && useradd -r -g opensshsync opensshsync
RUN chown -R opensshsync:opensshsync /app /data

# 切换到非root用户
USER opensshsync

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('https://mirrors.aliyun.com/openssh/portable', timeout=5)" || exit 1

# 设置入口点
ENTRYPOINT ["openssh-sync", "daemon"]