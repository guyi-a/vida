"""
基础设施模块
包含所有外部服务的基础设施封装
"""

# MinIO 对象存储
from .minio import MinioClient, minio_service

# Kafka 消息队列
from .kafka import kafka_client, kafka_service

# Celery 异步任务 - 延迟导入避免循环导入
# 如果需要使用 celery_app，请直接从 app.infra.celery 导入
# from .celery import celery_app


__all__ = [
    # MinIO
    "MinioClient",
    "minio_service",
    
    # Kafka
    "kafka_client",
    "kafka_service",
    
    # Celery - 已移除，请直接从 app.infra.celery 导入
    # "celery_app"
]