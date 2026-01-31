# vida

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

**访问服务：**
- API 服务：http://localhost:8000
- API 文档：http://localhost:8000/docs
- PostgreSQL：localhost:5432
- Redis：localhost:6379