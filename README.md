# TikTok Auto Spark

抖音自动续火花管理系统 - Docker 容器化版本

## 功能特性

- Web 管理界面（Vue 3 + Element Plus）
- 浏览器自动化（Selenium + Chromium）
- VNC 远程桌面（手动登录、实时查看）
- 定时任务管理（每日定时发送消息）
- 好友列表管理
- Docker 容器化部署

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus + Pinia |
| 后端 | Python FastAPI + Selenium |
| 浏览器 | Chromium + ChromeDriver |
| 桌面 | Xvfb + x11vnc + openbox |
| 部署 | Docker + docker-compose |

## 快速开始

### 使用 docker-compose（推荐）

```bash
# 克隆项目
git clone https://github.com/STAR-10086/TikTokAutoSparkWeb-STAR.git
cd TikTokAutoSparkWeb-STAR

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 访问服务

- **Web 管理界面**: http://localhost:8080
- **后端 API**: http://localhost:5000
- **VNC 远程桌面**: localhost:5900 (密码: 123456)

### 默认账号

- **用户名**: admin
- **密码**: 123456

## 使用说明

### 1. 初始化浏览器

登录 Web 管理界面后，进入「浏览器」页面，点击「初始化浏览器」按钮。

### 2. 登录抖音

有两种登录方式：

**方式一：扫码登录**
1. 点击「扫码登录」按钮
2. 使用 VNC Viewer 连接 `localhost:5900`
3. 在 VNC 桌面中查看浏览器显示的二维码
4. 使用抖音 APP 扫描二维码

**方式二：Cookie 登录**
1. 在 VNC 桌面中手动登录抖音
2. 通过 API 获取 Cookie
3. 在 Web 界面中导入 Cookie

### 3. 管理好友

登录成功后，进入「好友列表」页面，点击「刷新列表」获取好友信息。

### 4. 添加定时任务

进入「定时任务」页面，点击「添加任务」，选择好友和发送时间。

## 目录结构

```
TikTokAutoSparkWeb-STAR/
├── frontend/          # 前端代码
│   ├── src/           # Vue 源码
│   ├── Dockerfile     # 前端 Docker 配置
│   └── nginx.conf     # Nginx 配置
├── backend/           # 后端代码
│   ├── main.py        # FastAPI 主程序
│   ├── Dockerfile     # 后端 Docker 配置
│   └── requirements.txt
├── docker-compose.yml # Docker Compose 配置
└── .github/workflows/ # GitHub Actions
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| PORT | 5000 | 后端 API 端口 |
| ADMIN_PASSWORD | 123456 | 管理员密码 |
| DISPLAY_BROWSER | true | 是否显示浏览器窗口 |

## 端口说明

| 端口 | 服务 |
|------|------|
| 8080 | Web 管理界面 |
| 5000 | 后端 API |
| 5900 | VNC 远程桌面 |

## 从旧版本迁移

旧版本使用单体架构，新版本采用前后端分离架构：

- 前端独立部署在 Nginx
- 后端独立运行 FastAPI
- 通过 docker-compose 统一管理

## GitHub Actions

推送到 main 分支时自动构建 Docker 镜像：

- `ghcr.io/star-10086/tiktokautosparkweb-star-frontend:latest`
- `ghcr.io/star-10086/tiktokautosparkweb-star-backend:latest`

## 故障排查

### VNC 连接失败

```bash
# 检查 VNC 进程
docker exec tiktok-spark-backend ps aux | grep vnc
```

### 中文显示异常

```bash
# 重建字体缓存
docker exec tiktok-spark-backend fc-cache -fv
```

### 浏览器启动失败

```bash
# 检查 Chromium 版本
docker exec tiktok-spark-backend chromium --version
```

## License

MIT
