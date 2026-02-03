# Vida - 智能视频应用平台 🚀

**Vida** 是一个基于 FastAPI 构建的现代化视频应用平台，集成了用户管理、视频上传、转码处理、智能搜索、AI Agent 等核心功能，为短视频社交应用提供完整的后端解决方案。

## ✨ 核心特性

### 🎥 视频管理
- **视频上传**：支持大文件分片上传，自动存储到 MinIO 对象存储
- **视频转码**：基于 FFmpeg 的异步转码处理，支持多分辨率输出
- **视频管理**：完整的 CRUD 操作，支持视频信息编辑、删除
- **视频播放**：提供安全的视频播放 URL，支持 CDN 加速

### 👥 用户系统
- **用户认证**：基于 JWT 的 Token 认证机制
- **用户管理**：用户注册、登录、个人信息管理
- **用户关系**：关注/粉丝系统，支持双向关系管理
- **用户资料**：头像、横幅图片上传和管理

### 💬 社交功能
- **评论系统**：多级评论回复，支持评论点赞
- **收藏功能**：视频收藏和收藏夹管理
- **互动统计**：播放量、点赞数、评论数等实时统计

### 🔍 智能搜索
- **全文搜索**：基于 Elasticsearch 的全文检索，支持中文分词（IK 分词器）
- **AI Agent**：集成 LangGraph 的智能搜索 Agent，支持自然语言查询
- **多维度搜索**：支持按标题、描述、作者、时间范围等多维度搜索
- **智能排序**：相关性排序、时间排序、热度排序

### 🤖 AI Agent 服务
- **LangGraph 集成**：基于 LangGraph 构建的 Agent 工作流
- **工具调用**：支持搜索工具调用，可扩展更多工具
- **流式响应**：支持流式输出，提供更好的用户体验
- **上下文记忆**：支持对话上下文管理

### 🏗️ 技术架构
- **微服务架构**：基于 Docker Compose 的容器化部署
- **异步处理**：Celery 异步任务队列，支持视频转码等耗时操作
- **消息队列**：Kafka 消息队列，支持事件驱动架构
- **缓存系统**：Redis 缓存，提升系统性能
- **对象存储**：MinIO 对象存储，支持大规模文件存储

## 🛠️ 技术栈

### 后端框架
- **FastAPI** - 现代、快速的 Web 框架
- **SQLAlchemy** - Python ORM 框架（异步支持）
- **Pydantic** - 数据验证和设置管理

### 数据库与存储
- **PostgreSQL** - 主数据库（支持 pgvector 向量扩展）
- **Redis** - 缓存和 Celery 消息代理
- **MinIO** - 对象存储服务
- **Elasticsearch** - 全文搜索引擎（集成 IK 中文分词）

### 消息队列与任务
- **Kafka** - 分布式消息队列
- **Celery** - 分布式任务队列
- **Zookeeper** - Kafka 协调服务

### AI 与搜索
- **LangChain** - LLM 应用开发框架
- **LangGraph** - Agent 工作流框架
- **Elasticsearch** - 全文搜索引擎

### 视频处理
- **FFmpeg** - 视频转码和处理
- **ffmpeg-python** - FFmpeg Python 封装

### 安全认证
- **JWT** - JSON Web Token 认证
- **bcrypt** - 密码加密
- **passlib** - 密码哈希库

## 📁 项目结构

```
vida/
├── app/                    # 应用主目录
│   ├── api/               # API 路由
│   │   ├── auth.py        # 认证相关 API
│   │   ├── user.py        # 用户管理 API
│   │   ├── video.py       # 视频管理 API
│   │   ├── comment.py     # 评论 API
│   │   ├── favorite.py    # 收藏 API
│   │   ├── relation.py    # 用户关系 API
│   │   ├── search.py      # 搜索 API
│   │   └── agent.py       # AI Agent API
│   ├── agent/             # AI Agent 模块
│   │   ├── infra/         # Agent 基础设施
│   │   ├── service/       # Agent 服务
│   │   ├── tools/         # Agent 工具
│   │   └── prompts/       # 提示词模板
│   ├── core/              # 核心配置
│   │   ├── config.py      # 应用配置
│   │   ├── dependencies.py # 依赖注入
│   │   ├── middleware.py  # 中间件
│   │   └── exception.py   # 异常处理
│   ├── crud/              # 数据库操作层
│   ├── db/                # 数据库连接
│   ├── infra/             # 基础设施
│   │   ├── celery/        # Celery 配置
│   │   ├── elasticsearch/ # Elasticsearch 客户端
│   │   ├── kafka/         # Kafka 客户端
│   │   └── minio/         # MinIO 客户端
│   ├── models/            # 数据库模型
│   ├── schemas/           # Pydantic 模式
│   ├── tasks/             # Celery 任务
│   └── utils/             # 工具函数
├── static/                # 静态文件
├── scripts/               # 脚本文件
├── docs/                  # 文档
├── elasticsearch/         # Elasticsearch Dockerfile
├── docker-compose.yml     # Docker Compose 配置
├── Dockerfile             # Docker 镜像构建文件
├── main.py                # 应用入口
└── requirements.txt       # Python 依赖
```

## 🚀 快速开始

### 环境要求

- **Python** 3.10+
- **Docker** & **Docker Compose**
- **FFmpeg** (如果本地运行，需要单独安装)

### 1. 克隆项目

```bash
git clone <repository-url>
cd vida
```

### 2. 环境配置

创建 `.env` 文件（可选，使用默认配置）：

```env
# 数据库配置
DATABASE_URL=postgresql+asyncpg://guyi:guyi123@postgres:5432/guyi-vida

# Redis 配置
REDIS_URL=redis://redis:6379/0

# MinIO 配置
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Kafka 配置
KAFKA_BOOTSTRAP_SERVERS=kafka:29092

# Elasticsearch 配置
ELASTICSEARCH_HOSTS=elasticsearch:9200

# LLM 配置（AI Agent）
DASHSCOPE_API_KEY=your_api_key_here
LLM_MODEL=qwen-max

# JWT 配置
SECRET_KEY=your_secret_key_here
```

### 3. 使用 Docker Compose 启动（推荐）

启动所有服务：

```bash
docker-compose up -d
```

这将启动以下服务：
- **API 服务** (端口 8000)
- **PostgreSQL** (端口 5432)
- **Redis** (端口 6379)
- **MinIO** (API: 9000, Console: 9001)
- **Kafka** (端口 9092)
- **Zookeeper** (端口 2181)
- **Elasticsearch** (端口 9200)
- **Celery Worker** (异步任务处理)
- **Celery Beat** (定时任务调度)

### 4. 查看服务状态

```bash
# 查看所有服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f api
docker-compose logs -f celery_worker
```

### 5. 访问服务

- **API 文档**: http://localhost:8000/docs
- **API 交互式文档**: http://localhost:8000/redoc
- **MinIO 控制台**: http://localhost:9001 (用户名/密码: minioadmin/minioadmin)
- **Elasticsearch**: http://localhost:9200

## 💻 本地开发

### 1. 创建虚拟环境

```bash
python -m venv venv
```

### 2. 激活虚拟环境

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动数据库服务（使用 Docker Compose）

```bash
# 只启动数据库相关服务
docker-compose up -d postgres redis minio kafka zookeeper elasticsearch
```

### 5. 运行应用

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 运行 Celery Worker（另一个终端）

```bash
celery -A app.tasks:celery_app worker -l INFO -Q video_transcode,default
```

### 7. 运行 Celery Beat（定时任务，可选）

```bash
celery -A app.tasks:celery_app beat -l INFO
```

## 📚 API 文档

启动服务后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要 API 端点

#### 认证相关
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新 Token

#### 用户管理
- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新用户信息
- `GET /api/v1/users/{user_id}` - 获取用户信息

#### 视频管理
- `POST /api/v1/videos` - 上传视频
- `GET /api/v1/videos` - 获取视频列表
- `GET /api/v1/videos/{video_id}` - 获取视频详情
- `PUT /api/v1/videos/{video_id}` - 更新视频信息
- `DELETE /api/v1/videos/{video_id}` - 删除视频

#### 搜索功能
- `GET /api/v1/search/videos` - 搜索视频
- `POST /api/v1/search/sync` - 同步数据到 Elasticsearch

#### AI Agent
- `POST /api/v1/agent/chat` - AI Agent 对话（流式）
- `POST /api/v1/agent/chat/sync` - AI Agent 对话（同步）

## 🔧 配置说明

### 数据库初始化

应用启动时会自动创建数据库表结构。如果需要手动初始化：

```bash
# 进入 API 容器
docker-compose exec api bash

# 运行初始化脚本（如果有）
python scripts/init_db.py
```

### Elasticsearch 索引初始化

应用启动时会自动创建 Elasticsearch 索引。如果需要手动同步数据：

```bash
# 同步视频数据到 Elasticsearch
python scripts/sync_videos_to_es.py
```

### MinIO 存储桶

应用启动时会自动创建以下存储桶：
- `raw-videos` - 原始视频文件
- `public-videos` - 转码后的视频文件
- `user-avatars` - 用户头像
- `user-banners` - 用户横幅

## 🐳 Docker 命令参考

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 停止服务并删除数据卷（会删除数据库数据）
docker-compose down -v

# 重建并启动服务
docker-compose up -d --build

# 查看日志
docker-compose logs -f [service_name]

# 重启特定服务
docker-compose restart api

# 进入容器
docker-compose exec api bash
```

## 📝 开发指南

### 代码结构说明

- **API 层** (`app/api/`): 处理 HTTP 请求，定义路由和请求/响应模型
- **CRUD 层** (`app/crud/`): 数据库操作封装
- **模型层** (`app/models/`): SQLAlchemy 数据库模型
- **Schema 层** (`app/schemas/`): Pydantic 数据验证模型
- **基础设施层** (`app/infra/`): 第三方服务客户端封装
- **任务层** (`app/tasks/`): Celery 异步任务定义

### 添加新功能

1. **添加新的 API 端点**:
   - 在 `app/api/` 创建新的路由文件
   - 在 `main.py` 中注册路由

2. **添加新的数据库模型**:
   - 在 `app/models/` 定义模型
   - 在 `app/crud/` 创建 CRUD 操作
   - 在 `app/schemas/` 定义请求/响应模型

3. **添加新的异步任务**:
   - 在 `app/tasks/` 定义 Celery 任务
   - 使用 `@celery_app.task` 装饰器

### 测试

```bash
# 运行测试（如果有）
pytest

# 运行特定测试文件
pytest tests/test_video.py
```

## 🔒 安全说明

- **JWT Token**: 默认过期时间为 240 分钟，可在配置中修改
- **密码加密**: 使用 bcrypt 进行密码哈希
- **CORS**: 默认允许所有来源，生产环境请修改配置
- **Secret Key**: 生产环境请务必修改 `SECRET_KEY`

## 📊 监控与日志

- **日志级别**: 通过 `LOG_LEVEL` 环境变量配置（默认 INFO）
- **日志格式**: 结构化日志，包含时间戳、级别、消息
- **健康检查**: `GET /healthz` 端点用于健康检查

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情


