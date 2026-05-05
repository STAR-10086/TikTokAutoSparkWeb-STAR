# Docker 部署指南

## 快速开始

### 方式一：使用 docker-compose（推荐）

```bash
# 克隆项目
git clone https://github.com/STAR-10086/TikTokAutoSparkWeb-STAR.git
cd TikTokAutoSparkWeb-STAR

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 方式二：使用 docker run

```bash
# 构建镜像
docker build -t tiktok-spark .

# 运行容器
docker run -d \
  --name tiktok-spark \
  -p 5000:5000 \
  -p 5900:5900 \
  -v $(pwd)/data:/app/data \
  --shm-size=2gb \
  tiktok-spark
```

### 方式三：使用预构建镜像

```bash
docker run -d \
  --name tiktok-spark \
  -p 5000:5000 \
  -p 5900:5900 \
  -v $(pwd)/data:/app/data \
  --shm-size=2gb \
  ghcr.io/star-10086/tiktokautosparkweb-star:latest
```

---

## 端口说明

| 端口 | 服务 | 说明 |
|------|------|------|
| 5000 | Web API | FastAPI 后端服务，前端页面访问入口 |
| 5900 | VNC | 远程桌面，用于手动登录抖音 |

---

## VNC 连接方法

### 1. 安装 VNC Viewer

下载地址：https://www.realvnc.com/en/connect/download/viewer/

### 2. 连接容器

- **地址**：`localhost:5900` 或 `你的服务器IP:5900`
- **密码**：`123456`

### 3. 连接后操作

连接成功后会看到一个轻量级桌面环境（openbox），可以：

1. **手动打开 Chromium 浏览器**：
   ```bash
   # 在 VNC 桌面内右键打开终端，执行：
   chromium-browser --no-sandbox https://www.douyin.com
   ```

2. **扫码登录抖音**：
   - 打开抖音网页版
   - 使用手机抖音 APP 扫描二维码
   - 完成登录验证

3. **查看自动化操作**：
   - 通过 API 初始化浏览器后，可在 VNC 中实时查看浏览器操作

---

## 手动登录验证步骤

### 步骤 1：启动服务

```bash
docker-compose up -d
```

### 步骤 2：通过 VNC 手动登录

1. 使用 VNC Viewer 连接 `localhost:5900`，密码 `123456`
2. 在桌面内打开 Chromium 浏览器
3. 访问 `https://www.douyin.com`
4. 使用手机抖音扫码或验证码登录
5. 确保登录成功后保持浏览器打开

### 步骤 3：通过 API 操作

```bash
# 管理员登录获取 Token
curl "http://localhost:5000/Api/Login/Admin?username=admin&password=123456"

# 初始化浏览器（使用返回的 Token）
curl -H "Authorization: Bearer YOUR_TOKEN" "http://localhost:5000/Api/Init"

# 获取好友列表
curl -H "Authorization: Bearer YOUR_TOKEN" "http://localhost:5000/Api/GetFriendsList"
```

---

## 常用命令

```bash
# 查看容器状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

---

## 目录挂载

| 容器路径 | 主机路径 | 用途 |
|----------|----------|------|
| `/app/data` | `./data` | 持久化数据存储 |

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TZ` | `Asia/Shanghai` | 时区设置 |
| `PORT` | `5000` | Web 服务端口 |

---

## 从 Windows 迁移注意事项

### 1. 浏览器驱动

原项目使用 Windows 版 Edge 浏览器，Docker 容器已自动适配为：
- **Chromium** 浏览器
- **ChromeDriver** 驱动

### 2. 路径差异

原项目硬编码的 Windows 路径已在容器启动时自动替换：
- `C:\WebDriver\edge\msedgedriver.exe` → 系统默认 chromedriver
- `localhost` → `0.0.0.0`（容器内监听所有接口）

### 3. 交互式输入

原项目的 `input()` 交互已通过启动脚本自动处理：
- 浏览器显示模式：默认无头（通过 VNC 可见）
- 端口号：默认 5000

### 4. 中文显示

容器已安装完整中文字体：
- 文泉驿微米黑（WenQuanYi Micro Hei）
- 文泉驿正黑（WenQuanYi Zen Hei）

网页和浏览器中文显示正常，无需额外配置。

---

## GitHub Action 自动构建

项目配置了 GitHub Action，推送到 `main` 分支时自动构建多架构镜像：

- **平台**：`linux/amd64` + `linux/arm64`
- **仓库**：`ghcr.io/star-10086/tiktokautosparkweb-star`
- **标签**：`latest` + commit SHA

### 手动触发

在 GitHub 仓库页面 → Actions → "Build and Push Docker Image" → "Run workflow"

---

## 故障排查

### VNC 连接失败

```bash
# 检查 VNC 进程
docker exec tiktok-spark ps aux | grep vnc

# 重启 VNC
docker exec tiktok-spark x11vnc -display :99 -forever -shared -rfbauth ~/.vnc/password -rfbport 5900 &
```

### 中文显示方块

```bash
# 重建字体缓存
docker exec tiktok-spark fc-cache -fv

# 检查字体安装
docker exec tiktok-spark fc-list :lang=zh
```

### 浏览器启动失败

```bash
# 检查 Chromium 版本
docker exec tiktok-spark chromium-browser --version

# 检查 ChromeDriver 版本
docker exec tiktok-spark chromedriver --version
```

---

## 默认账号密码

| 服务 | 账号 | 密码 |
|------|------|------|
| Web 管理后台 | admin | 123456 |
| VNC 远程桌面 | - | 123456 |
