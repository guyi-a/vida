import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from app.core.config import settings
from app.core.middleware import LoggingMiddleware, TimingMiddleware, setup_cors_middleware
from app.core.exception import setup_exception_handlers
from app.db.database import init_db, close_db


# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


def start_kafka_consumer():
    """
    在后台线程中启动 Kafka 消费者
    """
    try:
        from app.infra.kafka.kafka_service import kafka_service
        logger.info("Starting Kafka consumer in background thread...")
        kafka_service.start_consumer()
    except Exception as e:
        logger.error(f"Failed to start Kafka consumer: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时初始化数据库和 Kafka 消费者，关闭时清理资源
    """
    # 启动时执行
    logger.info("Starting application...")
    try:
        # 初始化数据库
        await init_db()
        
        # 初始化Elasticsearch索引（新增）
        try:
            from app.infra.elasticsearch.es_client import get_es_client
            from app.infra.elasticsearch.index_manager import init_es_indexes
            
            es_client = get_es_client()
            init_es_indexes(es_client)
            logger.info("Elasticsearch索引初始化完成")
        except Exception as e:
            logger.warning(f"Elasticsearch索引初始化失败（可稍后手动创建）: {e}")
            # 不中断应用启动，允许后续手动创建索引
        
        # 在后台线程中启动 Kafka 消费者
        kafka_thread = threading.Thread(
            target=start_kafka_consumer,
            daemon=True,
            name="KafkaConsumerThread"
        )
        kafka_thread.start()
        logger.info("Kafka consumer thread started")
        
        logger.info("Application started successfully")
    except Exception as e:
        logger.error("Failed to initialize application: %s", str(e))
        raise
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Application shut down successfully")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="FastAPI application with database and Redis support",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# 设置中间件（注意顺序：后添加的先执行）
app.add_middleware(LoggingMiddleware)
app.add_middleware(TimingMiddleware)
setup_cors_middleware(app)  # CORS 中间件最后添加

# 设置异常处理器
setup_exception_handlers(app)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
from app.api.healthz import router as healthz_router
from app.api.test_middleware import router as test_middleware_router
from app.api.test_infra import router as test_infra_router
from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.api.video import router as video_router
from app.api.favorite import router as favorite_router
from app.api.comment import router as comment_router
from app.api.relation import router as relation_router
from app.api.search import router as search_router
from app.api.agent import router as agent_router

app.include_router(healthz_router)
app.include_router(test_middleware_router)
app.include_router(test_infra_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(video_router)
app.include_router(favorite_router)
app.include_router(comment_router)
app.include_router(relation_router)
app.include_router(search_router)
app.include_router(agent_router)


@app.get("/")
async def root():
    """根路径 - 返回前端页面"""
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": "Hello World",
        "project": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
    }


@app.get("/healthz")
async def healthz():
    """
    健康检查接口
    返回服务状态
    """
    return {"status": "ok", "message": "Service is healthy"}


@app.get("/favicon.ico")
async def favicon():
    """
    处理 favicon 请求
    返回 204 No Content，避免 404 错误
    """
    return Response(status_code=204)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )