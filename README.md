# Serv00 KeepAlive

[![Docker Build](https://github.com/maolei1024/serv00KeepAlive/actions/workflows/docker-build.yml/badge.svg)](https://github.com/maolei1024/serv00KeepAlive/actions/workflows/docker-build.yml)
[![Docker Pulls](https://img.shields.io/docker/pulls/maolei1024/serv00-keepalive)](https://hub.docker.com/r/maolei1024/serv00-keepalive)

自动登录 serv00 面板的保活工具，防止账号因 90 天不登录而被封禁。

## ✨ 功能特点

-  **HTTP 请求登录** - 轻量级，无需浏览器，资源消耗小
-  **账号状态检测** - 自动识别正常、封禁、登录失败等状态
-  **多账号支持** - 配置文件管理多个 serv00 账号
-  **封禁回调** - 账号被封时执行自定义 Shell 命令（发通知等）

## 📦 安装

### 方式 1：直接运行

```bash
# 克隆仓库
git clone https://github.com/maolei1024/serv00KeepAlive.git
cd serv00KeepAlive

# 安装依赖
pip install -r requirements.txt

# 复制并编辑配置文件
cp config.example.yaml config.yaml
# 编辑 config.yaml 填入你的账号信息
```

### 方式 2：Docker

```bash
# 从 Docker Hub 拉取
docker pull maolei1024/serv00-keepalive:latest
```

## 配置

复制示例配置文件并编辑：

```bash
cp config.example.yaml config.yaml
```

配置文件格式：

```yaml
accounts:
  - panel_url: "https://panel12.serv00.com"
    username: "your_username"
    password: "your_password"
    on_banned: null  # 可选：封禁时执行的命令

  - panel_url: "https://panel10.serv00.com"
    username: "another_user"
    password: "another_pass"
    on_banned: "curl -X POST https://your-webhook.com/alert"

settings:
  timeout: 30
  retry_count: 3
  log_file: "serv00.log"
```

##  运行

### 直接运行

```bash
python3 main.py
```

### 命令行选项

```
usage: main.py [-h] [-c CONFIG] [--no-log] [-v]

选项:
  -h, --help            显示帮助信息
  -c, --config CONFIG   配置文件路径 (默认: config.yaml)
  --no-log              不输出日志到文件
  -v, --verbose         显示详细输出
```

### Docker 运行

```bash
# 一次性运行
docker run --rm \
  -v $(pwd)/config.yaml:/app/config/config.yaml:ro \
  maolei1024/serv00-keepalive:latest

# 使用 docker-compose
docker-compose up
```

##  定时运行

### Cron（直接运行）

```bash
# 每周一早上 8 点执行
0 8 * * 1 cd /path/to/serv00KeepAlive && python3 main.py
```

### Cron + Docker

```bash
# 每周一早上 8 点执行
0 8 * * 1 docker run --rm -v /path/to/config.yaml:/app/config/config.yaml:ro maolei1024/serv00-keepalive
```


### 自行构建

```bash
# 构建
docker build -t serv00-keepalive .

# 运行
docker run --rm -v $(pwd)/config.yaml:/app/config/config.yaml:ro serv00-keepalive
```

## 📄 License

MIT
