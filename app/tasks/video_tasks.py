"""
视频相关Celery定时任务
"""

import logging
import asyncio
from typing import Dict, Any
from celery import shared_task
from app.infra.elasticsearch.es_client import get_es_client
from app.infra.elasticsearch.sync_service import calculate_hot_score
from app.crud.video_crud import video_crud
from app.core.config import settings
from app.db.database import async_session_maker

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 1})
def refresh_all_video_hot_score(self) -> Dict[str, Any]:
    """
    Celery定时任务：批量刷新所有已发布视频的hot_score（每小时执行一次）
    
    步骤：
    1. 批量查询数据库已发布视频
    2. 计算hot_score
    3. 批量更新ES（使用update操作）
    
    Returns:
        Dict: 任务执行结果
    """
    try:
        # 1. 获取ES客户端
        es_client = get_es_client()
        
        # 2. 批量查询数据库中所有已发布视频
        async def fetch_videos():
            async with async_session_maker() as db:
                return await video_crud.get_all_published_videos(db)
        
        published_videos = asyncio.run(fetch_videos())
        
        if not published_videos:
            logger.info("无已发布视频，跳过热度分数刷新")
            return {"status": "success", "message": "无已发布视频", "total": 0}
        
        logger.info(f"开始刷新 {len(published_videos)} 个视频的热度分数")
        
        # 3. 批量更新ES
        success_count = 0
        failed_count = 0
        
        for row in published_videos:
            try:
                # 3.1 动态计算最新hot_score
                hot_score = calculate_hot_score(
                    view_count=row.view_count or 0,
                    favorite_count=row.favorite_count or 0,
                    comment_count=row.comment_count or 0
                )
                
                # 3.2 更新ES文档（只更新hot_score字段）
                es_client.update(
                    index=settings.ELASTICSEARCH_INDEX_VIDEOS,
                    id=str(row.id),
                    body={
                        "doc": {
                            "hot_score": hot_score,
                            "updated_at": row.updated_at.isoformat() if row.updated_at else None
                        }
                    }
                )
                success_count += 1
                
            except Exception as e:
                logger.error(f"更新视频 {row.id} 热度分数失败: {e}")
                failed_count += 1
        
        logger.info(
            f"批量刷新热度分数完成：成功 {success_count} 个，失败 {failed_count} 个"
        )
        
        return {
            "status": "success",
            "message": f"成功刷新 {len(published_videos)} 个视频的热度分数",
            "total": len(published_videos),
            "success": success_count,
            "failed": failed_count
        }
    
    except Exception as e:
        logger.error(f"批量刷新热度分数任务失败: {e}", exc_info=True)
        raise

