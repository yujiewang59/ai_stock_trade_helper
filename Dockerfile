# FROM docker.mirrors.ustc.edu.cn/library/python:3.12-slim
FROM python:3.12-slim

# 安装系统依赖 + Redis
RUN apt-get update && apt-get install -y redis-server && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. 安装 uv（极速包管理器）
RUN pip install --no-cache-dir uv

# 安装 Python 依赖
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# 复制项目代码
COPY .env.example ./.env
COPY . .

# 暴露端口
EXPOSE 8000 8501 5555 6379

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf