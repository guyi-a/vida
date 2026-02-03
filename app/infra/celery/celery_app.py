"""
Celery应用配置
配置Celery异步任务队列
"""

from celery import Celery
from celery.signals import setup_logging
from celery.schedules import crontab
import logging
import os

from app.core.config import settings


def create_celery_app():
    """
    创建并配置Celery应用
    """
    # 创建Celery实例
    celery_app = Celery(
        'vida_tasks',
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND
    )
    
    # 基本配置
    celery_app.conf.update(
        # 序列化配置
        task_serializer=settings.CELERY_TASK_SERIALIZER,
        result_serializer=settings.CELERY_RESULT_SERIALIZER,
        accept_content=settings.CELERY_ACCEPT_CONTENT,
        
        # 时区配置
        timezone=settings.CELERY_TIMEZONE,
        enable_utc=True,
        
        # 任务配置
        task_track_started=True,
        task_time_limit=3600,  # 任务超时时间（秒）
        task_soft_time_limit=3300,  # 软超时时间
        task_acks_late=True,  # 任务执行完成后再确认
        worker_prefetch_multiplier=1,  # 一次只取一个任务
        
        # 队列配置
        task_default_queue='default',
        task_queues={
            'default': {
                'exchange': 'default',
                'exchange_type': 'direct',
                'routing_key': 'default'
            },
            'video_transcode': {
                'exchange': 'video_transcode',
                'exchange_type': 'direct',
                'routing_key': 'video_transcode'
            }
        },
        task_routes={
            'app.tasks.video_transcode.*': {
                'queue': 'video_transcode',
                'routing_key': 'video_transcode'
            },
            'app.tasks.db_update.*': {
                'queue': 'default',
                'routing_key': 'default'
            }
        },
        
        # Redis配置
        broker_transport_options={
            'visibility_timeout': 3600,  # 1小时
            'socket_timeout': 30,
            'socket_connect_timeout': 30,
            'retry_on_timeout': True
        },
        result_backend_transport_options={
            'socket_timeout': 30,
            'socket_connect_timeout': 30,
            'retry_on_timeout': True
        },
        
        # 结果过期时间（1天后自动删除）
        result_expires=86400,
        
        # 任务重试配置
        task_retry_kwargs={
            'max_retries': 3
        },
        task_retry_backoff=True,
        task_retry_backoff_max=600,
        task_retry_jitter=True,
        
        # Celery Beat定时任务配置
        beat_schedule={
            "refresh-video-hot-score-every-hour": {
                "task": "app.tasks.video_tasks.refresh_all_video_hot_score",
                "schedule": crontab(minute=0, hour="*/1"),  # 每小时整点执行
                "args": (),
                "options": {
                    "queue": "default"  # 使用默认队列
                }
            }
        }
    )
    
    # 自动发现任务
    celery_app.autodiscover_tasks(['app.tasks'], force=True)
    
    return celery_app


# 创建全局Celery应用实例
celery_app = create_celery_app()


@setup_logging.connect
def setup_celery_logging(**kwargs):
    """
    设置Celery日志
    """
    # 使用应用的日志配置
    pass


@celery_app.task(bind=True)
def debug_task(self):
    """
    调试任务
    """
    print(f'Request: {self.request!r}')


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def test_retry_task(self, message: str):
    """
    测试重试的任务
    """
    print(f"执行重试测试任务: {message}")
    if not hasattr(self, '_retry_count'):
        self._retry_count = 0
    
    self._retry_count += 1
    
    if self._retry_count < 3:
        print(f"模拟失败，重试计数: {self._retry_count}")
        raise Exception("模拟失败")
    
    print(f"任务成功完成！")
    return f"重试测试成功: {message}"