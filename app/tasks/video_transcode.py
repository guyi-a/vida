"""
视频转码任务
使用Celery和FFmpeg处理视频转码
"""

from celery import shared_task, current_task
from celery.exceptions import SoftTimeLimitExceeded
import ffmpeg
import os
import tempfile
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import shutil

from app.core.config import settings
from app.infra.minio import MinioClient, minio_service


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2})
def video_transcode_task(
    self,
    video_id: int,
    raw_object_name: str,
    user_id: int,
    quality: str = '720p',
    format: str = 'mp4',
    generate_cover: bool = True,
    **kwargs
):
    """
    视频转码任务
    
    Args:
        video_id: 视频ID
        raw_object_name: 原始视频对象名称
        user_id: 用户ID
        quality: 转码质量 (480p, 720p, 1080p)
        format: 输出格式
        generate_cover: 是否生成封面
        **kwargs: 额外参数
    
    Returns:
        转码结果
    """
    logger = logging.getLogger(__name__)
    
    # 更新任务状态
    current_task.update_state(state='PROCESSING', meta={
        'stage': 'preparing',
        'video_id': video_id,
        'progress': 0
    })
    
    temp_dir = None
    raw_file_path = None
    output_file_path = None
    cover_file_path = None
    
    try:
        # 1. 准备临时目录
        temp_dir = tempfile.mkdtemp(prefix=f"transcode_{video_id}_")
        raw_file_path = os.path.join(temp_dir, f"raw_{video_id}.mp4")
        output_file_path = os.path.join(temp_dir, f"output_{video_id}.{format}")
        
        logger.info(f"视频转码开始 - Video ID: {video_id}")
        
        # 2. 下载原始视频
        current_task.update_state(state='PROCESSING', meta={
            'stage': 'downloading',
            'video_id': video_id,
            'progress': 10
        })
        
        try:
            minio_client.download_file(
                object_name=raw_object_name,
                bucket_name=settings.MINIO_RAW_BUCKET,
                file_path=raw_file_path
            )
            logger.info(f"原始视频下载完成: {raw_file_path}")
        except Exception as e:
            raise Exception(f"下载原始视频失败: {e}")
        
        # 3. 验证视频文件
        if not os.path.exists(raw_file_path):
            raise Exception("原始视频文件不存在")
        
        file_size = os.path.getsize(raw_file_path)
        if file_size == 0:
            raise Exception("原始视频文件为空")
        
        # 4. 执行转码
        current_task.update_state(state='PROCESSING', meta={
            'stage': 'transcoding',
            'video_id': video_id,
            'progress': 30
        })
        
        # 根据质量设置参数
        quality_settings = get_quality_settings(quality)
        
        try:
            stream = ffmpeg.input(raw_file_path)
            
            # 转码参数
            stream = ffmpeg.output(
                stream,
                output_file_path,
                **quality_settings,
                format=format,
                acodec='aac',
                audio_bitrate='128k'
            )
            
            # 执行转码
            logger.info(f"开始转码 - Quality: {quality}, Format: {format}")
            ffmpeg.run(stream, overwrite_output=True, capture_stderr=True)
            logger.info(f"视频转码完成: {output_file_path}")
            
        except ffmpeg.Error as e:
            error_message = e.stderr.decode('utf-8') if e.stderr else str(e)
            raise Exception(f"FFmpeg转码失败: {error_message}")
        
        # 5. 生成封面（如果需要）
        if generate_cover:
            current_task.update_state(state='PROCESSING', meta={
                'stage': 'generating_cover',
                'video_id': video_id,
                'progress': 70
            })
            
            cover_file_path = os.path.join(temp_dir, f"cover_{video_id}.jpg")
            
            try:
                stream = ffmpeg.input(raw_file_path, ss='00:00:01.000')  # 第1秒处截图
                stream = ffmpeg.output(
                    stream,
                    cover_file_path,
                    vframes=1,
                    s='1280x720'  # 封面尺寸
                )
                
                ffmpeg.run(stream, overwrite_output=True, capture_stderr=True)
                logger.info(f"封面生成完成: {cover_file_path}")
                
            except ffmpeg.Error as e:
                logger.warning(f"封面生成失败: {e}")
                cover_file_path = None
        
        # 6. 上传到MinIO公共桶
        current_task.update_state(state='PROCESSING', meta={
            'stage': 'uploading',
            'video_id': video_id,
            'progress': 85
        })
        
        # 上传转码后的视频
        with open(output_file_path, 'rb') as video_file:
            video_upload_result = minio_service.publish_video(
                file_obj=video_file,
                filename=f"video_{video_id}.{format}",
                user_id=user_id
            )
        
        cover_upload_result = None
        if cover_file_path and os.path.exists(cover_file_path):
            with open(cover_file_path, 'rb') as cover_file:
                cover_upload_result = minio_service.upload_video_cover(
                    file_obj=cover_file,
                    filename=f"cover_{video_id}.jpg",
                    user_id=user_id,
                    video_object_name=video_upload_result['object_name']
                )
        
        # 7. 更新数据库（通过异步任务）
        current_task.update_state(state='PROCESSING', meta={
            'stage': 'updating_database',
            'video_id': video_id,
            'progress': 95
        })
        
        # 触发数据库更新任务
        update_video_metadata.delay(
            video_id=video_id,
            play_url=video_upload_result['public_url'],
            cover_url=cover_upload_result['public_url'] if cover_upload_result else None,
            status='published',
            file_size=os.path.getsize(output_file_path),
            duration=get_video_duration(raw_file_path)
        )
        
        # 8. 返回结果
        result = {
            'task_id': current_task.request.id,
            'video_id': video_id,
            'status': 'completed',
            'quality': quality,
            'format': format,
            'play_url': video_upload_result['public_url'],
            'cover_url': cover_upload_result['public_url'] if cover_upload_result else None,
            'file_size': os.path.getsize(output_file_path),
            'duration': get_video_duration(raw_file_path),
            'completed_at': __import__('time').time()
        }
        
        current_task.update_state(state='SUCCESS', meta={
            'stage': 'completed',
            'video_id': video_id,
            'progress': 100,
            'result': result
        })
        
        logger.info(f"视频转码任务完成 - Video ID: {video_id}")
        return result
        
    except SoftTimeLimitExceeded:
        logger.error(f"视频转码任务超时 - Video ID: {video_id}")
        raise Exception("转码任务执行超时")
        
    except Exception as e:
        logger.error(f"视频转码任务失败 - Video ID: {video_id}, Error: {e}")
        
        # 更新任务状态为失败
        current_task.update_state(
            state='FAILURE',
            meta={
                'video_id': video_id,
                'error': str(e),
                'exc_type': type(e).__name__,
                'failed_at': __import__('time').time()
            }
        )
        raise
        
    finally:
        # 清理临时文件
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"清理临时目录: {temp_dir}")
            except Exception as e:
                logger.warning(f"清理临时目录失败: {e}")


def get_quality_settings(quality: str) -> Dict[str, Any]:
    """
    根据质量获取FFmpeg转码参数
    
    Args:
        quality: 转码质量
        
    Returns:
        FFmpeg参数字典
    """
    settings_map = {
        '480p': {
            'vf': 'scale=-2:480',
            'vcodec': 'libx264',
            'video_bitrate': '1000k',
            'bufsize': '2000k'
        },
        '720p': {
            'vf': 'scale=-2:720',
            'vcodec': 'libx264',
            'video_bitrate': '2500k',
            'bufsize': '5000k'
        },
        '1080p': {
            'vf': 'scale=-2:1080',
            'vcodec': 'libx264',
            'video_bitrate': '5000k',
            'bufsize': '10000k'
        }
    }
    
    if quality not in settings_map:
        raise ValueError(f"不支持的转码质量: {quality}")
    
    return settings_map[quality]


def get_video_duration(file_path: str) -> Optional[int]:
    """
    获取视频时长（秒）
    
    Args:
        file_path: 视频文件路径
        
    Returns:
        视频时长（秒）
    """
    try:
        probe = ffmpeg.probe(file_path)
        duration = float(probe['format']['duration'])
        return int(duration)
    except Exception as e:
        logging.getLogger(__name__).warning(f"获取视频时长失败: {e}")
        return None