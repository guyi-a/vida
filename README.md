# Vida - 视频应用平台 🚀

**Vida** 是一个基于 FastAPI 构建的现代化视频应用平台，集成了用户管理、视频上传、转码处理等核心功能，为短视频社交应用提供完整的后端解决方案。

## 项目进展

### ✅ 已完成功能

#### 核心认证系统
- **用户注册** `POST /api/v1/auth/register` - 新用户账号创建
- **用户登录** `POST /api/v1/auth/login` - JWT token认证
- **获取用户信息** `GET /api/v1/auth/me` - 当前用户数据查询
- **密码安全** - 使用 bcrypt 哈希加密存储

#### 用户管理系统
- **用户信息管理** - 支持头像、用户名、背景图更新
- **用户数据查询** - 个人信息和公开资料访问
- **权限控制** - 角色基础访问控制(RBAC)
- **用户列表管理** `(管理员)` - 用户搜索、筛选、分页

#### 健壮架构设计
- **异步数据库操作** - SQLAlchemy + async/await
- **中间件系统** - 请求日志、性能监控、CORS配置
- **异常处理** - 统一的错误响应格式
- **配置管理** - 环境变量驱动的应用配置

#### 开发运维支持
- **Docker容器化** - 一键部署开发环境
- **健康检查** - 服务健康状态监控
- **日志记录** - 结构化日志便于问题排查
- **API文档** - Swagger UI 自动生成接口文档

### 📋 待开发功能

#### 视频核心功能 （规划中）
- [ ] 视频上传接口
- [ ] 异步视频转码
- [ ] 视频流(刷视频)接口
- [ ] 互动功能(点赞、评论)

## 技术栈

### 核心框架
- **FastAPI** - 现代化、快速、易用的Web框架
- **Pydantic** - 数据验证和设置管理
- **SQLAlchemy** - 功能强大的ORM工具

### 数据库与存储
- **PostgreSQL** - 稳定可靠的关系型数据库
- **Redis** - 高性能缓存和会话管理

### 安全与认证
- **JWT** - JSON Web Token认证
- **Passlib** - 密码哈希加密
- **OAuth2** - 行业标准认证协议

### 开发与部署
- **Docker** - 容器化部署
- **Uvicorn** - 高性能ASGI服务器
- **Python 3.10+** - 最新Python特性支持

## 🚀 快速开始

## 虚拟环境配置

### 创建虚拟环境（已完成）
```bash
python -m venv venv
```

### 激活虚拟环境

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 安装依赖
```bash
pip install -r requirements.txt
```

### 退出虚拟环境
```bash
deactivate
```

### 启动项目

**本地开发（不使用 Docker）：**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**使用 Docker Compose：**

启动所有服务（API、PostgreSQL、Redis）：
```bash
docker-compose up -d
```

查看服务状态：
```bash
docker-compose ps
```

查看日志：
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f redis
```

停止服务：
```bash
docker-compose down
```

停止服务并删除数据卷（会删除数据库数据）：
```bash
docker-compose down -v
```

重建并启动服务：
```bash
docker-compose up -d --build
```

重启特定服务：
```bash
docker-compose restart api
```

## 📚 API 文档

启动服务后，访问以下文档：

- **Swagger UI**: http://localhost:8000/docs - 交互式API文档
- **ReDoc**: http://localhost:8000/redoc - 替代文档格式

### 健康检查端点
- `GET /healthz` - 基础健康检查
- `GET /api/v1/healthz` - API级健康检查
- `GET /test/middleware` - 中间件功能测试

### 认证相关端点
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息
- `POST /api/v1/auth/logout` - 用户登出

### 用户管理端点
- `GET /api/v1/users/me` - 获取当前用户详情
- `PUT /api/v1/users/{user_id}` - 更新用户信息
- `GET /api/v1/users` - 获取用户列表（管理员权限）
- `DELETE /api/v1/users/{user_id}` - 删除用户（管理员权限）

## 🏗️ 项目结构

```
vida/
├── app/                           # 应用主模块
│   ├── api/                      # API路由层
│   │   ├── auth.py              # 认证相关API
│   │   ├── user.py              # 用户管理API
│   │   ├── healthz.py           # 健康检查API  
│   │   └── test_middleware.py   # 中间件测试API
│   ├── core/                     # 核心功能模块
│   │   ├── config.py            # 应用配置
│   │   ├── dependencies.py      # 依赖注入
│   │   ├── exception.py         # 异常定义
│   │   ├── exception_handlers.py # 异常处理器
│   │   ├── middleware.py        # 中间件
│   │   └── logging_config.py    # 日志配置
│   ├── db/                       # 数据库模块
│   │   └── database.py          # 数据库连接与操作
│   ├── crud/                     # CRUD操作层
│   │   ├── __init__.py
│   │   └── user_crud.py         # 用户相关CRUD
│   ├── models/                   # 数据模型层
│   │   ├── __init__.py
│   │   └── user.py              # 用户模型
│   ├── schemas/                 # Pydantic模型层
│   │   ├── request/             # 请求模型
│   │   │   ├── auth_request.py
│   │   │   └── user_request.py
│   │   └── response/            # 响应模型
│   │       ├── base_response.py
│   │       └── auth_response.py
│   └── utils/                    # 工具模块
│       └── security.py          # 安全相关工具
├── docs/                         # 项目文档
└── main.py                       # 应用入口
```

## 🧪 测试与验证

### API功能测试
项目已通过完整的API测试验证，包括：
- ✅ 用户注册与登录功能
- ✅ JWT认证与权限控制
- ✅ 用户信息管理
- ✅ 中间件功能
- ✅ 异常处理机制

### 性能特性
- **异步处理** - 支持高并发请求
- **连接池** - 数据库连接复用
- **缓存支持** - Redis缓存集成
- **日志追踪** - 完整的请求响应追踪

## 🔧 环境配置

### 必需环境变量

创建 `.env` 文件配置以下变量：

```env
# 数据库配置
DATABASE_URL=postgresql+asyncpg://guyi:guyi123@localhost:5432/guyi-vida

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=240

# API配置
API_V1_PREFIX=/api/v1
PROJECT_NAME=Vida
PROJECT_VERSION=0.1.0

# 服务配置
DEBUG=True
LOG_LEVEL=INFO

# CORS配置
CORS_ORIGINS=["*"]
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=["*"]
CORS_ALLOW_HEADERS=["*"]
```

### 依赖管理

核心依赖包括：
- `fastapi==0.104.1` - Web框架
- `uvicorn==0.24.0` - ASGI服务器
- `sqlalchemy==2.0.23` - ORM
- `pydantic==2.5.0` - 数据验证
- `alembic==1.12.1` - 数据库迁移
- `python-jose[cryptography]==3.3.0` - JWT处理
- `passlib[bcrypt]==1.7.4` - 密码加密
- `python-multipart==0.0.6` - 文件上传
- `psycopg2-binary==2.9.9` - PostgreSQL驱动
- `asyncpg==0.29.0` - 异步PostgreSQL驱动
- `redis==5.0.1` - Redis客户端

**访问服务：**
- **API 服务**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🚀 下一步开发计划

详细的视频功能开发计划详见 [docs/视频功能开发计划.md](docs/视频功能开发计划.md)