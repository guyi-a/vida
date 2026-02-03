"""
Elasticsearch数据同步服务
提供视频数据同步到ES的功能
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from elasticsearch import Elasticsearch
from app.core.config import settings
from app.infra.elasticsearch.es_client import get_es_client

logger = logging.getLogger(__name__)


def calculate_hot_score(view_count: int, favorite_count: int, comment_count: int) -> float:
    """
    计算视频热度分数
    
    公式：hot_score = (view_count * 0.5 + favorite_count * 2.0 + comment_count * 1.5) / 1000
    
    Args:
        view_count: 播放量
        favorite_count: 点赞数
        comment_count: 评论数
        
    Returns:
        float: 热度分数
    """
    return (view_count * 0.5 + favorite_count * 2.0 + comment_count * 1.5) / 1000


def video_to_es_document(video: Any, author_name: Optional[str] = None) -> Dict[str, Any]:
    """
    将视频模型转换为ES文档格式
    
    Args:
        video: Video模型对象
        author_name: 作者名称（可选）
        
    Returns:
        dict: ES文档数据（只包含搜索字段，不包括URL）
    """
    # 计算热度分数
    hot_score = calculate_hot_score(
        view_count=video.view_count or 0,
        favorite_count=video.favorite_count or 0,
        comment_count=video.comment_count or 0
    )
    
    # 转换时间格式
    created_at = None
    if video.created_at:
        if isinstance(video.created_at, datetime):
            created_at = video.created_at.isoformat()
        else:
            created_at = str(video.created_at)
    
    updated_at = None
    if video.updated_at:
        if isinstance(video.updated_at, datetime):
            updated_at = video.updated_at.isoformat()
        else:
            updated_at = str(video.updated_at)
    
    # 构建ES文档（只包含搜索字段，不包括play_url和cover_url）
    doc = {
        "id": video.id,
        "author_id": video.author_id,
        "author_name": author_name or "",
        "title": video.title or "",
        "description": video.description or "",
        "status": video.status or "pending",
        "publish_time": video.publish_time or 0,
        "view_count": video.view_count or 0,
        "favorite_count": video.favorite_count or 0,
        "comment_count": video.comment_count or 0,
        "hot_score": hot_score,
        "duration": video.duration or 0,
        "created_at": created_at,
        "updated_at": updated_at
    }
    
    return doc


async def sync_video_to_es(
    video: Any,
    author_name: Optional[str] = None,
    es_client: Optional[Elasticsearch] = None
) -> bool:
    """
    同步单个视频到ES
    
    Args:
        video: Video模型对象
        author_name: 作者名称（可选）
        es_client: ES客户端实例，如果为None则自动获取
        
    Returns:
        bool: 同步是否成功
    """
    if es_client is None:
        try:
            es_client = get_es_client()
        except Exception as e:
            logger.error(f"无法获取ES客户端: {e}")
            return False
    
    try:
        doc = video_to_es_document(video, author_name)
        index_name = settings.ELASTICSEARCH_INDEX_VIDEOS
        
        # 使用视频ID作为ES文档ID
        es_client.index(
            index=index_name,
            id=str(video.id),
            body=doc
        )
        
        logger.debug(f"视频 {video.id} 同步到ES成功")
        return True
        
    except Exception as e:
        logger.error(f"同步视频 {video.id} 到ES失败: {e}", exc_info=True)
        return False


async def delete_video_from_es(
    video_id: int,
    es_client: Optional[Elasticsearch] = None
) -> bool:
    """
    从ES删除视频文档
    
    Args:
        video_id: 视频ID
        es_client: ES客户端实例，如果为None则自动获取
        
    Returns:
        bool: 删除是否成功
    """
    if es_client is None:
        try:
            es_client = get_es_client()
        except Exception as e:
            logger.error(f"无法获取ES客户端: {e}")
            return False
    
    try:
        index_name = settings.ELASTICSEARCH_INDEX_VIDEOS
        es_client.delete(index=index_name, id=str(video_id))
        logger.debug(f"视频 {video_id} 从ES删除成功")
        return True
        
    except Exception as e:
        # 如果文档不存在，也算成功（幂等性）
        if "not_found" in str(e).lower():
            logger.debug(f"视频 {video_id} 在ES中不存在，跳过删除")
            return True
        logger.error(f"从ES删除视频 {video_id} 失败: {e}", exc_info=True)
        return False


async def update_video_in_es(
    video: Any,
    author_name: Optional[str] = None,
    es_client: Optional[Elasticsearch] = None
) -> bool:
    """
    更新ES中的视频文档
    
    Args:
        video: Video模型对象
        author_name: 作者名称（可选）
        es_client: ES客户端实例，如果为None则自动获取
        
    Returns:
        bool: 更新是否成功
    """
    # 更新操作和创建操作相同（ES的index操作是upsert）
    return await sync_video_to_es(video, author_name, es_client)


async def bulk_sync_videos_to_es(
    videos: List[Any],
    author_names: Optional[Dict[int, str]] = None,
    es_client: Optional[Elasticsearch] = None
) -> Dict[str, int]:
    """
    批量同步视频到ES
    
    Args:
        videos: Video模型对象列表
        author_names: 作者名称字典 {author_id: author_name}
        es_client: ES客户端实例，如果为None则自动获取
        
    Returns:
        dict: 同步结果统计 {"success": 成功数, "failed": 失败数}
    """
    if es_client is None:
        try:
            es_client = get_es_client()
        except Exception as e:
            logger.error(f"无法获取ES客户端: {e}")
            return {"success": 0, "failed": len(videos)}
    
    if author_names is None:
        author_names = {}
    
    success_count = 0
    failed_count = 0
    index_name = settings.ELASTICSEARCH_INDEX_VIDEOS
    
    # 准备bulk操作
    bulk_operations = []
    for video in videos:
        try:
            author_name = author_names.get(video.author_id, None)
            doc = video_to_es_document(video, author_name)
            
            # 添加index操作
            bulk_operations.append({
                "index": {
                    "_index": index_name,
                    "_id": str(video.id)
                }
            })
            bulk_operations.append(doc)
            
        except Exception as e:
            logger.error(f"准备视频 {video.id} 的bulk操作失败: {e}")
            failed_count += 1
    
    # 执行bulk操作
    if bulk_operations:
        try:
            # 使用ES的bulk API
            response = es_client.bulk(body=bulk_operations)
            
            if response.get("errors"):
                # 统计成功和失败的数量
                for item in response.get("items", []):
                    if "index" in item:
                        if item["index"].get("status") in [200, 201]:
                            success_count += 1
                        else:
                            failed_count += 1
                    elif "update" in item:
                        if item["update"].get("status") in [200, 201]:
                            success_count += 1
                        else:
                            failed_count += 1
            else:
                success_count = len(videos)
            
            logger.info(f"批量同步完成: 成功 {success_count} 个，失败 {failed_count} 个")
            
        except Exception as e:
            logger.error(f"批量同步到ES失败: {e}", exc_info=True)
            failed_count += len(videos) - success_count
    
    return {"success": success_count, "failed": failed_count}

