# 使用轻量级 Python 镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 复制依赖文件
COPY requirements.txt .

# 安装系统工具（curl 用于 webhook 通知等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY main.py serv00_login.py logger.py ./

# 创建配置目录和日志目录
RUN mkdir -p /app/config /app/logs

# 默认配置文件位置
ENV CONFIG_PATH=/app/config/config.yaml
ENV LOG_PATH=/app/logs/serv00.log

# 运行脚本
# ENTRYPOINT 固定执行 python3 main.py
# CMD 提供默认参数，可被 K8s args 覆盖
ENTRYPOINT ["python3", "main.py"]
CMD ["-c", "/app/config/config.yaml"]
