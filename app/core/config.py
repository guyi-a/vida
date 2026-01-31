from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    应用配置设置
    """
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://guyi:guyi123@localhost:5432/guyi-vida"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 应用配置
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    


    # API配置
    API_VERSION: str = "0.1.0"
    PROJECT_NAME: str = "Vida API"
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_VERSION: str = "0.1.0"





    # CORS配置
    CORS_ORIGINS: list = ["*"]  # 允许的来源
    CORS_ALLOW_CREDENTIALS: bool = True  # 允许携带凭据
    CORS_ALLOW_METHODS: list = ["*"]  # 允许的HTTP方法
    CORS_ALLOW_HEADERS: list = ["*"]  # 允许的HTTP头





    # 日志配置
    LOG_LEVEL: str = "INFO"  # 日志级别
    
    # JWT配置
    SECRET_KEY: str = "guyi"  # JWT密钥
    ALGORITHM: str = "HS256"  # JWT算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 240  # Token过期时间（分钟）

    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# 创建全局设置实例
settings = Settings()