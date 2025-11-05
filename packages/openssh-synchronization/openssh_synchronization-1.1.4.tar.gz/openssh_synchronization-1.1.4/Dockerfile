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

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    patchelf \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 安装Nuitka和项目依赖
RUN pip install --no-cache-dir nuitka
RUN pip install --no-cache-dir -e .

# 使用Nuitka打包应用（打包入口脚本）
RUN python -m nuitka \
    --standalone \
    --onefile \
    --output-filename=openssh-sync \
    --follow-imports \
    entry.py

# 第二阶段：运行时阶段（使用更小的基础镜像）
FROM python:3.11-slim AS runtime

# 设置清华镜像源
RUN sed -i 's|http://deb.debian.org/debian|http://mirrors.tuna.tsinghua.edu.cn/debian|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|http://deb.debian.org/debian-security|http://mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list.d/debian.sources

# 安装运行时依赖（仅需要基本系统工具）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建非root用户
RUN groupadd -r opensshsync && useradd -r -g opensshsync opensshsync

# 创建应用目录和数据目录
RUN mkdir -p /app /data/openssh

# 从构建阶段复制打包好的可执行文件
COPY --from=builder /app/openssh-sync /app/openssh-sync

# 设置环境变量
ENV DOWNLOAD_DIR=/data/openssh
ENV CHECK_INTERVAL=24
ENV MIN_VERSION=10.2.1
ENV DEBUG=false

# 设置镜像版本信息
ARG VERSION=1.1.4
LABEL version="${VERSION}"
LABEL description="OpenSSH synchronization tool version ${VERSION}"

# 设置目录权限
RUN chown -R opensshsync:opensshsync /app /data

# 切换到非root用户
USER opensshsync

# 设置工作目录
WORKDIR /app

# 设置健康检查（使用curl替代Python）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://mirrors.tuna.tsinghua.edu.cn/openssh/portable || exit 1

# 设置入口点
ENTRYPOINT ["/app/openssh-sync", "daemon"]