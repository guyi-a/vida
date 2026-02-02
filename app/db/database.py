import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from sqlalchemy.orm import declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)


# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 开发环境打印 SQL
    future=True,
    pool_pre_ping=True,  # 连接池健康检查
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
)


# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# 创建基础模型类
Base = declarative_base()


async def init_db():
    """
    初始化数据库
    创建所有表结构
    """
    async with engine.begin() as conn:
        # 先尝试删除可能存在的旧冲突索引（如果存在）
        old_indexes = [
            "idx_created_at",  # 旧的通用 created_at 索引
            "idx_user_id",     # 旧的通用 user_id 索引
            "idx_video_id",   # 旧的通用 video_id 索引
        ]
        for index_name in old_indexes:
            try:
                await conn.execute(text(f'DROP INDEX IF EXISTS "{index_name}"'))
                logger.info(f"Dropped old index: {index_name}")
            except Exception as e:
                logger.debug(f"Index {index_name} does not exist or already dropped: {e}")
        
        # 创建所有表结构
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    关闭数据库连接
    """
    await engine.dispose()


async def get_db():
    """
    获取数据库会话的依赖函数
    用于 FastAPI 依赖注入
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()