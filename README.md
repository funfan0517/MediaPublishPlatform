# 自媒体智能运营系统 (SAU)

## 项目地址

[GitHub 仓库](https://github.com/fan-0517/SAU.git)

## 项目介绍

SAU (Social Auto Upload) 是一个功能强大的自媒体智能运营系统，支持图文和视频内容的批量上传与定时发布，帮助内容创作者实现多平台自动化运营。

### 主要特点

- **多平台支持**：覆盖主流自媒体平台，包括小红书、腾讯视频号、抖音、快手、TikTok、Instagram等
- **自动化发布**：基于 Playwright 的浏览器自动化技术，实现无人值守发布
- **批量操作**：支持多文件批量上传和多账号轮换发布
- **定时发布**：灵活的定时发布功能，支持自定义发布时间和发布频率
- **统一管理**：提供统一的Web界面，集中管理所有发布任务
- **易于扩展**：模块化设计，便于添加新平台支持

## 项目架构

### 后端架构

后端采用模块化设计，基于 Flask 框架构建 RESTful API 服务，结合 Playwright 实现浏览器自动化上传，核心组件包括：

1. **核心上传引擎** (`sau_backend/newFileUpload/baseFileUploader.py`)
   - 通用多平台上传器基类，定义了统一的上传接口和流程
   - 支持多平台配置（小红书、腾讯、抖音、快手、TikTok、Instagram 等）
   - 使用 Playwright 实现浏览器自动化操作
   - 支持图文和视频两种内容类型
   - 提供定时发布、标签管理等核心功能

2. **多文件上传处理** (`sau_backend/newFileUpload/multiFileUploader.py`)
   - 批量文件处理，支持多账号轮换
   - 自动生成发布计划时间
   - 异步执行上传任务
   - 提供完整的发布结果反馈

3. **Flask 后端服务** (`sau_backend/sau_backend.py`)
   - RESTful API 接口设计
   - 文件上传、保存和查询功能
   - 支持跨域请求
   - 数据库集成，记录文件上传历史
   - 提供用户认证和权限管理

4. **平台配置管理** (`sau_backend/newFileUpload/platform_configs.py`)
   - 集中管理各平台配置（类型、URL、选择器等）
   - 提供平台类型与标识的映射函数
   - 便于添加新平台支持

5. **旧版上传实现** (`sau_backend/oldFileUpload/`)
   - 各平台独立的上传器实现
   - 包含完整的登录和上传功能
   - 作为备用方案，确保系统稳定性

### 前端架构

前端基于 Vue 3 + Element Plus 构建，提供直观易用的用户界面：

- **响应式设计**：适配不同屏幕尺寸
- **现代化界面**：使用 Element Plus 组件库，提供美观的用户体验
- **实时状态反馈**：发布任务状态实时更新
- **文件管理**：可视化的文件上传和管理界面
- **账号管理**：集中管理所有平台账号

## 项目结构

```
sau/
├── README.md              # 项目说明文档
├── start-win.bat          # Windows 启动脚本
├── requirements.txt       # Python 依赖包
├── sau_backend/           # 后端项目
│   ├── README.md          # 后端说明文档
│   ├── conf.example.py    # 配置文件示例
│   ├── conf.py            # 配置文件（需自行创建）
│   ├── sau_backend.py     # 后端主入口文件
│   ├── myUtils/           # 核心工具模块
│   │   ├── auth.py        # 认证相关功能
│   │   └── login.py       # 登录相关功能
│   ├── newFileUpload/     # 新版文件上传实现
│   │   ├── baseFileUploader.py    # 通用上传器基类
│   │   ├── multiFileUploader.py   # 多文件上传处理
│   │   └── platform_configs.py    # 平台配置
│   ├── oldFileUpload/     # 旧版文件上传实现
│   │   ├── examples/      # 示例脚本
│   │   └── uploader/      # 各平台上传器实现
│   └── utils/             # 工具函数
│       ├── base_social_media.py   # 社交媒体基础功能
│       ├── log.py                 # 日志管理
│       └── stealth.min.js         # 浏览器隐藏脚本
├── sau_frontend/          # 前端项目
│   ├── src/               # 前端源代码
│   ├── public/            # 静态资源
│   ├── package.json       # npm 配置
│   └── vite.config.js     # Vite 配置
├── db/                    # 数据库相关
│   ├── database.db        # SQLite 数据库文件
│   └── createTable.py     # 数据库初始化脚本
├── cookiesFile/           # 存储 Cookie 文件
├── videoFile/             # 存储上传的视频文件
└── videos/                # 示例视频文件
```

## 技术栈

### 后端技术

- **Web 框架**: Flask 2.0+
- **浏览器自动化**: Playwright 1.30+
- **数据库**: SQLite 3
- **异步处理**: asyncio
- **文件管理**: pathlib
- **日志管理**: 自定义日志模块
- **API 设计**: RESTful API

### 前端技术

- **框架**: Vue 3
- **构建工具**: Vite
- **UI 组件库**: Element Plus
- **状态管理**: Pinia
- **HTTP 客户端**: Axios
- **CSS 预处理器**: SCSS

## 核心功能

### 1. 多平台支持

- ✅ 小红书
- ✅ 腾讯视频号
- ✅ 抖音
- ✅ 快手
- ✅ TikTok
- ✅ Instagram
- ✅ Facebook

### 2. 内容类型支持

- ✅ 视频文件上传
- ✅ 图文内容发布
- ✅ 封面设置（部分平台）

### 3. 发布功能

- ✅ 即时发布
- ✅ 定时发布，支持自定义发布时间
- ✅ 批量发布，支持多账号轮换
- ✅ 发布计划管理

### 4. 管理功能

- ✅ 文件上传和管理
- ✅ 发布历史记录
- ✅ 账号管理（添加、编辑、删除）
- ✅ Cookie 管理（上传、下载）

### 5. 系统功能

- ✅ 跨域支持
- ✅ 错误处理
- ✅ 日志记录
- ✅ 状态反馈

## 安装指南

### 1. 克隆项目

```bash
git clone https://github.com/fan-0517/SAU.git
cd SAU
```

### 2. 安装依赖

建议在虚拟环境中安装依赖：

#### 使用 Conda（推荐）

```bash
conda create -n sau python=3.10
conda activate sau
# 挂载清华镜像加速安装
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 使用 venv

```bash
python -m venv venv
# Windows
env\Scripts\activate
# Linux/MacOS
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 安装 Playwright 浏览器驱动

```bash
playwright install chromium firefox
```

根据您的需求，至少需要安装 `chromium`。`firefox` 主要用于 TikTok 上传（旧版）。

### 4. 配置文件

复制 `sau_backend/conf.example.py` 并重命名为 `sau_backend/conf.py`：

```bash
cp sau_backend/conf.example.py sau_backend/conf.py
```

在 `sau_backend/conf.py` 中，您需要配置以下内容：

- `LOCAL_CHROME_PATH`: 本地 Chrome 浏览器的路径，例如：
  - Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`
  - Linux: `/usr/bin/google-chrome`
  - MacOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`

### 5. 创建必要的文件夹

```bash
mkdir -p cookiesFile videoFile
```

- `cookiesFile`: 存储 Cookie 文件
- `videoFile`: 存储上传的视频文件

### 6. 配置数据库

如果 `db/database.db` 文件不存在，您可以运行以下命令来初始化数据库：

```bash
cd db
python createTable.py
cd ..
```

此命令将初始化 SQLite 数据库，创建必要的表结构。

### 7. 启动后端服务

```bash
cd sau_backend
python sau_backend.py
```

后端服务将在 `http://localhost:5409` 启动。

### 8. 启动前端项目

```bash
cd sau_frontend
npm install
npm run dev
```

前端项目将在 `http://localhost:5173` 启动，在浏览器中打开此链接即可访问。

### 9. 快速启动（Windows）

对于 Windows 用户，您可以使用项目根目录下的 `start-win.bat` 脚本快速启动前后端服务：

```bash
start-win.bat
```

此脚本将自动激活虚拟环境（如果存在）并启动后端服务。

## 快速开始

### 1. 登录系统

打开浏览器，访问 `http://localhost:5173`，进入系统登录页面。

### 2. 添加账号

1. 点击左侧导航栏的「账号管理」
2. 点击「添加账号」按钮
3. 选择平台类型
4. 按照提示完成登录操作
5. 系统会自动保存 Cookie 并创建账号

### 3. 上传文件

1. 点击左侧导航栏的「文件管理」
2. 点击「上传文件」按钮
3. 选择要上传的视频或图片文件
4. 等待上传完成

### 4. 发布内容

1. 点击左侧导航栏的「发布中心」
2. 选择要发布的文件
3. 选择发布平台和账号
4. 填写标题、正文和标签
5. 设置发布时间（可选）
6. 点击「发布」按钮，系统将自动执行发布任务


## API 文档

### 后端 API 接口

#### 账号管理

- `GET /getAccounts` - 获取所有账号信息
- `GET /getValidAccounts` - 获取有效的账号信息（带 Cookie 验证）
- `POST /account` - 添加账号
- `POST /updateUserinfo` - 更新账号信息
- `GET /deleteAccount?id={id}` - 删除账号
- `GET /downloadCookie?filePath={filePath}` - 下载 Cookie 文件
- `POST /uploadCookie` - 上传 Cookie 文件

#### 文件管理

- `POST /upload` - 上传文件
- `GET /getFiles` - 获取文件列表

#### 发布管理

- `POST /postVideosToMultiplePlatforms` - 发布视频到多个平台
- `GET /getPlatformStats` - 获取平台账号统计

## 技术实现细节

### 浏览器自动化

系统使用 Playwright 库实现浏览器自动化，主要流程包括：

1. 启动浏览器实例
2. 加载平台登录页面
3. 使用存储的 Cookie 进行登录
4. 导航到发布页面
5. 自动填充发布信息（标题、正文、标签等）
6. 上传媒体文件
7. 执行发布操作
8. 验证发布结果

### 定时发布实现

定时发布功能通过以下方式实现：

1. 计算发布时间点
2. 创建发布任务队列
3. 使用线程池执行定时任务
4. 任务执行时唤醒浏览器并执行发布操作

### 多账号轮换

系统支持多账号轮换发布，实现方式：

1. 为每个平台维护账号池
2. 发布时按顺序或随机选择账号
3. 记录每个账号的使用情况
4. 避免单个账号发布频率过高

## 常见问题

### 1. Cookie 过期怎么办？

当 Cookie 过期时，系统会自动检测到并标记账号状态为「失效」。您需要重新登录该账号以更新 Cookie：

1. 在账号管理页面，找到状态为「失效」的账号
2. 点击「重新登录」按钮
3. 按照提示完成登录操作
4. 系统会自动更新 Cookie 并恢复账号状态

### 2. 发布失败怎么办？

发布失败可能有多种原因，您可以：

1. 查看发布历史中的错误信息
2. 检查账号状态是否正常
3. 检查网络连接是否稳定
4. 确认平台是否有发布限制
5. 尝试重新发布

### 3. 如何添加新平台支持？

要添加新平台支持，您需要：

1. 在 `sau_backend/newFileUpload/platform_configs.py` 中添加平台配置
2. 在 `sau_backend/myUtils/login.py` 中添加登录逻辑
3. 在 `sau_backend/myUtils/auth.py` 中添加 Cookie 验证逻辑

### 4. 系统运行缓慢怎么办？

系统运行缓慢可能是由于：

1. 浏览器实例启动过多
2. 发布任务队列过长
3. 系统资源不足

解决方案：
- 减少同时执行的发布任务数量
- 增加系统内存和 CPU 资源
- 优化网络连接

## 贡献指南

我们欢迎社区贡献，包括但不限于：

1. **代码贡献**：提交 Pull Request 来修复 bug 或添加新功能
2. **平台支持**：添加对新平台的支持
3. **文档完善**：改进文档，添加使用示例
4. **问题反馈**：报告 bug 或提出新功能建议

### 贡献流程

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 代码规范

- 遵循 PEP 8 代码规范（Python）
- 遵循 ESLint 代码规范（JavaScript/TypeScript）
- 为新功能添加测试用例
- 确保代码通过所有测试

## 部署方案

### 本地开发环境

按照「安装指南」中的步骤部署到本地机器。

### Docker 部署

1. 构建 Docker 镜像：

```bash
docker build -t sau .
```

2. 运行 Docker 容器：

```bash
docker run -d -p 5409:5409 -p 5173:5173 --name sau sau
```

3. 访问应用：

打开浏览器，访问 `http://localhost:5173`

### 生产环境部署

1. 构建前端项目：

```bash
cd sau_frontend
npm run build
```

2. 配置后端服务：

- 修改 `sau_backend/conf.py` 中的配置
- 配置反向代理（如 Nginx）
- 设置环境变量

3. 启动服务：

使用 Supervisor 或 Systemd 管理服务进程。

## 许可证

本项目采用 MIT 许可证：

```
MIT License

Copyright (c) 2026 SAU 项目团队

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 鸣谢

- [Flask](https://flask.palletsprojects.com/) - Python Web 框架
- [Playwright](https://playwright.dev/) - 现代浏览器自动化库
- [Vue 3](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Element Plus](https://element-plus.org/) - 基于 Vue 3 的 UI 组件库
- [SQLite](https://www.sqlite.org/) - 轻量级数据库

## 联系方式

- **GitHub Issues**：[https://github.com/fan-0517/SAU/issues](https://github.com/fan-0517/SAU/issues)
- **Email**：1424393744@qq.com

## 更新日志

### v1.0.0 (2026-01-13)

- ✨ 初始版本发布
- ✅ 支持小红书、腾讯视频号、抖音、快手、TikTok、Instagram 平台
- ✅ 实现视频和图文发布功能
- ✅ 支持定时发布和批量发布
- ✅ 提供完整的 Web 管理界面
- ✅ 实现新版文件上传系统（通用基类 + 平台配置）
- ✅ 保留旧版文件上传系统作为备用

---

**感谢使用 SAU 自媒体智能运营系统！** 🚀

如果您觉得这个项目对您有帮助，请给我们一个 ⭐️ 支持一下！
