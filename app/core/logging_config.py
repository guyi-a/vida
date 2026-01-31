"""
日志配置
"""
import logging
import logging.config
from .config import settings
import os


def setup_logging():
    """
    配置应用日志
    """
    # 确保日志目录存在
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 日志配置文件
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            },
            "access": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "formatter": "default",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": f"{log_dir}/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "access_file": {
                "formatter": "access",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": f"{log_dir}/access.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["default", "file"],
                "level": "INFO",
                "propagate": False
            },
            "uvicorn": {
                "handlers": ["default", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["access_file"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy": {
                "handlers": ["default", "file"],
                "level": "WARNING",  # SQLAlchemy日志级别
                "propagate": False,
            },
        },
    }
    
    # 根据环境调整日志级别
    if settings.DEBUG:
        LOGGING_CONFIG["loggers"][""] = {
            "handlers": ["default", "file"],
            "level": "DEBUG",
            "propagate": False
        }
        LOGGING_CONFIG["loggers"]["sqlalchemy"]["level"] = "INFO"
    
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # 设置根日志级别
    logging.getLogger().setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)