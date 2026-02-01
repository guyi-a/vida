"""
异步任务模块
包含Celery任务和异步操作
"""

# 从infra导入Celery应用
from ..infra.celery.celery_app import celery_app

# 导出任务
from .video_transcode import video_transcode_task
from .db_update import (
    update_video_metadata,
    increment_video_stats,
    update_user_stats,
    batch_update_stats,
    cleanup_temp_files
)

__all__ = [
    'celery_app',
    'video_transcode_task',
    'update_video_metadata',
    'increment_video_stats',
    'update_user_stats',
    'batch_update_stats',
    'cleanup_temp_files'
]