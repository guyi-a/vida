"""
数据库更新任务
使用Celery异步更新数据库记录
"""

from celery import shared_task, current_task
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.models.user import User


@shared_task(bind=True)
def update_video_metadata(
    self,
    video_id: int,
    play_url: str,
    status: str,
    file_size: Optional[int] = None,
    duration: Optional[int] = None,
    cover_url: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    更新视频元数据
    
    Args:
        video_id: 视频ID
        play_url: 播放URL
        status: 视频状态
        file_size: 文件大小
        duration: 视频时长
        cover_url: 封面URL
        **kwargs: 额外参数
        
    Returns:
        更新结果
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"开始更新视频元数据 - Video ID: {video_id}")
        
        # 更新任务进度
        current_task.update_state(state='PROCESSING', meta={
            'stage': 'updating_video_metadata',
            'video_id': video_id
        })
        
        # TODO: 实际项目中需要导入Video模型和执行数据库更新
        # 这里仅演示结构
        
        # async with AsyncSessionLocal() as session:
        #     # 查找视频记录
        #     result = await session.execute(
        #         select(Video).where(Video.id == video_id)
        #     )
        #     video = result.scalar_one_or_none()
        #     
        #     if not video:
        #         raise Exception(f"视频记录不存在: {video_id}")
        #     
        #     # 更新字段
        #     video.play_url = play_url
        #     video.cover_url = cover_url
        #     video.status = status
        #     video.file_size = file_size
        #     video.duration = duration
        #     video.updated_at = datetime.utcnow()
        #     
        #     await session.commit()
        
        # 模拟更新成功
        result = {
            'task_id': self.request.id,
            'video_id': video_id,
            'updated_fields': {
                'play_url': play_url,
                'cover_url': cover_url,
                'status': status,
                'file_size': file_size,
                'duration': duration
            },
            'updated_at': datetime.now().timestamp()
        }
        
        logger.info(f"视频元数据更新完成 - Video ID: {video_id}")
        return result
        
    except Exception as e:
        logger.error(f"更新视频元数据失败 - Video ID: {video_id}, Error: {e}")
        
        current_task.update_state(
            state='FAILURE',
            meta={
                'video_id': video_id,
                'error': str(e),
                'exc_type': type(e).__name__
            }
        )
        raise


@shared_task(bind=True)
def increment_video_stats(
    self,
    video_id: int,
    stat_type: str,  # 'view', 'favorite', 'comment'
    increment: int = 1
) -> Dict[str, Any]:
    """
    增加视频统计信息
    
    Args:
        video_id: 视频ID
        stat_type: 统计类型
        increment: 增量值
        
    Returns:
        更新结果
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"增加视频统计 - Video ID: {video_id}, Type: {stat_type}")
        
        valid_stats = ['view_count', 'favorite_count', 'comment_count']
        if stat_type not in valid_stats:
            raise ValueError(f"无效的统计类型: {stat_type}")
        
        # TODO: 实际数据库更新
        # async with AsyncSessionLocal() as session:
        #     result = await session.execute(
        #         select(Video).where(Video.id == video_id)
        #     )
        #     video = result.scalar_one_or_none()
        #     
        #     if video:
        #         setattr(video, stat_type, getattr(video, stat_type) + increment)
        #         await session.commit()
        
        result = {
            'task_id': self.request.id,
            'video_id': video_id,
            'stat_type': stat_type,
            'increment': increment,
            'completed_at': datetime.now().timestamp()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"增加视频统计失败 - Video ID: {video_id}, Error: {e}")
        raise


@shared_task(bind=True)
def update_user_stats(
    self,
    user_id: int,
    stat_type: str,  # 'follow_count', 'follower_count', 'video_count'
    increment: int = 1
) -> Dict[str, Any]:
    """
    更新用户统计信息（关注数、粉丝数等）
    
    Args:
        user_id: 用户ID
        stat_type: 统计类型
        increment: 增量值
        
    Returns:
        更新结果
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"更新用户统计 - User ID: {user_id}, Type: {stat_type}")
        
        valid_stats = ['follow_count', 'follower_count', 'video_count']
        if stat_type not in valid_stats:
            raise ValueError(f"无效的用户统计类型: {stat_type}")
        
        # TODO: 实际数据库更新
        # async with AsyncSessionLocal() as session:
        #     result = await session.execute(
        #         select(User).where(User.id == user_id)
        #     )
        #     user = result.scalar_one_or_none()
        #     
        #     if user:
        #         current_value = getattr(user, stat_type, 0)
        #         setattr(user, stat_type, current_value + increment)
        #         await session.commit()
        
        result = {
            'task_id': self.request.id,
            'user_id': user_id,
            'stat_type': stat_type,
            'increment': increment,
            'completed_at': datetime.now().timestamp()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"更新用户统计失败 - User ID: {user_id}, Error: {e}")
        raise


@shared_task(bind=True)
def batch_update_stats(
    self,
    operations: list
) -> Dict[str, Any]:
    """
    批量更新统计信息
    提高性能，减少数据库操作次数
    
    Args:
        operations: 操作列表，每个操作包含必要的参数
        
    Returns:
        批量更新结果
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"批量更新统计信息 - 操作数量: {len(operations)}")
        
        # 更新任务进度
        total_ops = len(operations)
        completed_ops = 0
        
        results = []
        
        for op in operations:
            try:
                op_type = op.get('type')
                
                if op_type == 'video_stats':
                    result = increment_video_stats(
                        video_id=op['video_id'],
                        stat_type=op['stat_type'],
                        increment=op.get('increment', 1)
                    )
                elif op_type == 'user_stats':
                    result = update_user_stats(
                        user_id=op['user_id'],
                        stat_type=op['stat_type'],
                        increment=op.get('increment', 1)
                    )
                else:
                    raise ValueError(f"未知的批量操作类型: {op_type}")
                
                results.append(result)
                completed_ops += 1
                
                # 更新进度
                progress = int((completed_ops / total_ops) * 100)
                current_task.update_state(
                    state='PROCESSING',
                    meta={
                        'completed': completed_ops,
                        'total': total_ops,
                        'progress': progress
                    }
                )
                
            except Exception as e:
                logger.error(f"批量操作失败 - Operation: {op}, Error: {e}")
                results.append({
                    'operation': op,
                    'error': str(e),
                    'status': 'failed'
                })
        
        final_result = {
            'task_id': self.request.id,
            'total_operations': total_ops,
            'completed_operations': completed_ops,
            'results': results,
            'completed_at': datetime.now().timestamp()
        }
        
        logger.info(f"批量更新完成 - Completed: {completed_ops}/{total_ops}")
        return final_result
        
    except Exception as e:
        logger.error(f"批量更新任务失败 - Error: {e}")
        raise


@shared_task(bind=True)
def cleanup_temp_files(
    self,
    file_paths: list
) -> Dict[str, Any]:
    """
    清理临时文件
    
    Args:
        file_paths: 要清理的文件路径列表
        
    Returns:
        清理结果
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"开始清理临时文件 - 文件数量: {len(file_paths)}")
        
        deleted_count = 0
        failed_count = 0
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"删除临时文件: {file_path}")
                else:
                    logger.debug(f"文件不存在，跳过: {file_path}")
            except Exception as e:
                failed_count += 1
                logger.error(f"删除文件失败: {file_path}, Error: {e}")
        
        result = {
            'task_id': self.request.id,
            'total_files': len(file_paths),
            'deleted_files': deleted_count,
            'failed_files': failed_count,
            'completed_at': datetime.now().timestamp()
        }
        
        logger.info(f"临时文件清理完成 - Deleted: {deleted_count}, Failed: {failed_count}")
        return result
        
    except Exception as e:
        logger.error(f"清理临时文件任务失败 - Error: {e}")
        raise