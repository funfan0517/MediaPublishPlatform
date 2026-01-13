## 启动项目：
python 版本：3.10
1. 安装依赖
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
2. 删除 db 目录下 database.db（如果没有直接运行createTable.py即可），运行 createTable.py 重新建库，避免出现脏数据
3. 修改 conf.py最下方 LOCAL_CHROME_PATH 为本地 chrome 浏览器地址
4. 运行根目录的 sau_backend.py
5. type字段（平台标识） 1 小红书 2 视频号 3 抖音 4 快手

## 文件上传实现说明

### 新版文件上传（推荐）

**目录：** `e:\Ai\AiTools\sau\sau_backend\newFileUpload`

**核心文件：**
- `baseFileUploader.py` - 通用多平台上传器基类
- `multiFileUploader.py` - 多文件批量上传处理
- `platform_configs.py` - 平台配置管理

**设计特点：**
1. **统一基类架构**：采用通用 `BaseFileUploader` 基类，所有平台共享相同的上传流程
2. **集中配置管理**：通过 `platform_configs.py` 集中管理所有平台的配置信息
3. **模块化设计**：上传逻辑与平台配置分离，便于维护和扩展
4. **多平台支持**：支持小红书、视频号、抖音、快手、TikTok、Instagram、Facebook 等平台
5. **统一接口**：所有平台使用相同的上传接口，简化调用方式

**使用方式：**
通过调用 `multiFileUploader.py` 中的 `post_multiple_files_to_multiple_platforms` 函数，一次性上传多个文件到多个平台。

### 旧版文件上传

**目录：** `e:\Ai\AiTools\sau\sau_backend\oldFileUpload`

**核心结构：**
- `examples/` - 各平台上传示例脚本
- `uploader/` - 各平台独立上传器实现

**设计特点：**
1. **平台独立实现**：每个平台有独立的上传器类和实现逻辑
2. **硬编码配置**：平台特定配置硬编码在各自的上传器类中
3. **分散式结构**：代码分散在多个平台目录中，结构较为复杂
4. **平台支持**：支持小红书、视频号、抖音、快手、TikTok、B站、百家号等平台
5. **独立调用**：每个平台需要单独调用对应的上传器

**使用方式：**
通过调用各平台上传器的实例方法，如 `xhsVideoUploader`、`douyin_uploader` 等。

### 新旧版本对比

| 特性 | 新版文件上传 | 旧版文件上传 |
|------|-------------|-------------|
| 架构设计 | 通用基类 + 平台配置 | 平台独立实现 |
| 代码组织 | 集中式，核心文件少 | 分散式，文件数量多 |
| 配置管理 | 集中配置文件 | 硬编码在各平台类中 |
| 扩展性 | 高，添加新平台只需修改配置 | 低，添加新平台需要创建新类 |
| 平台支持 | 小红书、视频号、抖音、快手、TikTok、Instagram、Facebook | 小红书、视频号、抖音、快手、TikTok、B站、百家号 |
| 调用方式 | 统一接口，批量处理 | 独立调用，逐个处理 |
| 维护成本 | 低，核心逻辑集中 | 高，平台代码分散 |
| 推荐使用 | ✅ 推荐 | ⚠️ 仅用于兼容旧代码 |

### 如何选择

1. **新项目开发**：推荐使用新版文件上传实现，享受统一架构和集中配置的优势
2. **现有项目兼容**：如果需要兼容旧代码或特定平台的旧实现，可以使用旧版文件上传
3. **添加新平台**：建议在新版实现中添加，通过修改 `platform_configs.py` 即可
4. **批量发布需求**：新版实现支持批量文件和多平台发布，更适合批量操作场景

## 接口说明
1. /upload post
    上传接口，上传成功会返回文件的唯一id，后期靠这个发布视频
2. /login id参数 用户名 type参数 平台标识：登录流程，前端和后端建立sse连接，后端获取到图片base64编码后返回给前端，前端接受扫码后后端存库后返回200，前端主动断开连接，然后调取/getValidAccounts获取当前所有可用账号
3. /getValidAccounts 会获取当前所有可用cookie，时间较慢，会逐个校验cookie，status 1 有效 0 无效cookie
4. /postVideo 发布视频接口 post json传参
    file_list      /upload获取的文件唯一标识
    account_list   /getValidAccounts获取的filePath字段
    type           类型字段（平台标识）
    title          视频标题
    tags           视频tag 列表，不带#
    category       原作者说是原创表示，0表示不是原创其他表示为原创，但测试该字段没有效果
    enableTimer    是否开启定时发布，默认关闭，开启传True，如果开启，下面三个必传，否则不传
    videos_per_day 每天发布几个视频
    daily_times    每天发布视频的时间，整形列表，与上面列表长度保持一致
    start_days     开始天数，0 代表明天开始定时发布 1 代表明天的明天
    以上三个字段是我的理解，不知道对不对，也不知道原作者为什么要这么设置

## 数据库说明
见当前目录下 db目录，py文件是创建脚本，db文件是sqlite数据库

## 文件说明
cookiesFile文件夹 存储cookie文件
myUtils文件夹 存储自己封装的python模块
videoFile文件夹 文件上传存放位置
web 文件夹 web路由目录
conf.py 全局配置，记得修改配置中 LOCAL_CHROME_PATH 为本机浏览器地址

## 平台标识对照表

| 平台 | type字段值 | 平台标识 | 新版支持 | 旧版支持 |
|------|-----------|---------|---------|---------|
| 小红书 | 1 | xiaohongshu | ✅ | ✅ |
| 腾讯视频号 | 2 | tencent | ✅ | ✅ |
| 抖音 | 3 | douyin | ✅ | ✅ |
| 快手 | 4 | kuaishou | ✅ | ✅ |
| TikTok | 5 | tiktok | ✅ | ✅ |
| Instagram | 6 | instagram | ✅ | ❌ |
| Facebook | 7 | facebook | ✅ | ❌ |
| B站 | 8 | bilibili | ❌ | ✅ |
| 百家号 | 9 | baijiahao | ❌ | ✅ |