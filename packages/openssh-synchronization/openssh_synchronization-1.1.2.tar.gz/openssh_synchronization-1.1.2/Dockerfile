# OpenSSH同步工具Docker镜像 - 多阶段构建
# 第一阶段：构建阶段
FROM python:3.11-slim AS builder

# 设置清华镜像源以加速下载
RUN sed -i 's|http://deb.debian.org/debian|http://mirrors.tuna.tsinghua.edu.cn/debian|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|http://deb.debian.org/debian-security|http://mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list.d/debian.sources

# 设置pip清华镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 安装构建工具和依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境
RUN python -m venv /opt/venv

# 激活虚拟环境并安装依赖
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -e .

# 第二阶段：运行时阶段
FROM python:3.11-slim AS runtime

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建非root用户
RUN groupadd -r opensshsync && useradd -r -g opensshsync opensshsync

# 创建应用目录和数据目录
RUN mkdir -p /app /data/openssh

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 从构建阶段复制项目文件（仅需要部分文件）
COPY --from=builder /app/openssh_sync /app/openssh_sync
COPY --from=builder /app/pyproject.toml /app/
COPY --from=builder /app/README.md /app/

# 设置环境变量
ENV PATH="/opt/venv/bin:$PATH"
ENV DOWNLOAD_DIR=/data/openssh
ENV CHECK_INTERVAL=24
ENV MIN_VERSION=10.2.1
ENV DEBUG=false
ENV PYTHONPATH=/app

# 设置目录权限
RUN chown -R opensshsync:opensshsync /app /data

# 切换到非root用户
USER opensshsync

# 设置工作目录
WORKDIR /app

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('https://mirrors.aliyun.com/openssh/portable', timeout=5)" || exit 1

# 设置入口点
ENTRYPOINT ["openssh-sync", "daemon"]