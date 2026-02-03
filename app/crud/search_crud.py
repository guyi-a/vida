"""
搜索CRUD模块
提供视频搜索功能
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from elasticsearch import Elasticsearch
from app.models.video import Video
from app.schemas.request.search_request import SearchRequest
from app.schemas.response.search_response import SearchResponse, SearchVideoResponse
from app.infra.elasticsearch.es_client import get_es_client
from app.core.config import settings

logger = logging.getLogger(__name__)


async def search_videos(
    db: AsyncSession,
    query_params: SearchRequest,
    es_client: Optional[Elasticsearch] = None
) -> SearchResponse:
    """
    搜索视频（ES查询ID，然后批量查询数据库获取完整信息）
    
    Args:
        db: 数据库会话
        query_params: 搜索请求参数
        es_client: ES客户端实例，如果为None则自动获取
        
    Returns:
        SearchResponse: 搜索结果
    """
    if es_client is None:
        try:
            es_client = get_es_client()
        except Exception as e:
            logger.error(f"无法获取ES客户端: {e}")
            # 降级到数据库搜索
            return await _fallback_db_search(db, query_params)
    
    try:
        # 1. 构建ES查询（只返回ID和排序信息）
        es_query = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": [
                        {"term": {"status": "published"}}
                    ]
                }
            },
            "_source": ["id"],  # 只返回ID字段，减少数据传输
            "from": (query_params.page - 1) * query_params.page_size,
            "size": query_params.page_size
        }
        
        # 添加全文搜索条件
        if query_params.q:
            # 根据关键词长度调整匹配策略
            query_text = query_params.q.strip()
            # 对于短关键词（1-2个字），使用更宽松的匹配
            # 对于长关键词，使用更严格的匹配
            if len(query_text) <= 2:
                # 短关键词：使用 should 而不是 must，降低匹配要求
                es_query["query"]["bool"]["should"] = [{
                    "multi_match": {
                        "query": query_text,
                        "fields": ["title^3", "description^1"],
                        "type": "best_fields",
                        "operator": "or"
                    }
                }]
                es_query["query"]["bool"]["minimum_should_match"] = 1
            else:
                # 长关键词：使用 must，提高匹配精度
                es_query["query"]["bool"]["must"].append({
                    "multi_match": {
                        "query": query_text,
                        "fields": ["title^3", "description^1"],
                        "type": "best_fields",
                        "operator": "or",
                        "minimum_should_match": "50%"
                    }
                })
        
        # 添加结构化匹配条件
        if query_params.author_id:
            es_query["query"]["bool"]["filter"].append({
                "term": {"author_id": query_params.author_id}
            })
        
        if query_params.video_id:
            es_query["query"]["bool"]["filter"].append({
                "term": {"id": query_params.video_id}
            })
        
        # 添加时间范围过滤
        if query_params.start_time or query_params.end_time:
            time_range = {}
            if query_params.start_time:
                time_range["gte"] = query_params.start_time
            if query_params.end_time:
                time_range["lte"] = query_params.end_time
            es_query["query"]["bool"]["filter"].append({
                "range": {"publish_time": time_range}
            })
        
        # 添加排序
        sort_config = []
        if query_params.sort == "relevance":
            sort_config.append({"_score": {"order": "desc"}})
        elif query_params.sort == "hot":
            sort_config.append({"hot_score": {"order": "desc"}})
        elif query_params.sort == "time":
            sort_config.append({"publish_time": {"order": "desc"}})
        else:
            # 默认：相关性 + 时间
            sort_config.append({"_score": {"order": "desc"}})
            sort_config.append({"publish_time": {"order": "desc"}})
        
        es_query["sort"] = sort_config
        
        # 添加高亮（如果有关键词搜索）
        if query_params.q:
            es_query["highlight"] = {
                "fields": {
                    "title": {},
                    "description": {}
                },
                "pre_tags": ["<em>"],
                "post_tags": ["</em>"]
            }
        
        # 2. 执行ES查询
        # Elasticsearch 8.x 支持 body 参数，但需要确保客户端版本正确
        # 如果遇到版本兼容性问题，可以尝试使用 query 参数
        try:
            es_response = es_client.search(
                index=settings.ELASTICSEARCH_INDEX_VIDEOS,
                body=es_query
            )
        except Exception as e:
            # 如果 body 参数失败，尝试使用新的 API 格式
            logger.warning(f"使用 body 参数失败，尝试新的 API 格式: {e}")
            es_response = es_client.search(
                index=settings.ELASTICSEARCH_INDEX_VIDEOS,
                query=es_query.get("query"),
                _source=es_query.get("_source"),
                from_=es_query.get("from", 0),
                size=es_query.get("size", 20),
                sort=es_query.get("sort"),
                highlight=es_query.get("highlight")
            )
        
        # 3. 提取视频ID列表（保持ES返回的顺序）
        hits = es_response["hits"]["hits"]
        video_ids = [hit["_source"]["id"] for hit in hits]
        # ES 8.x 返回格式：total 可能是数字或对象
        total_info = es_response["hits"]["total"]
        if isinstance(total_info, dict):
            total = total_info["value"]
        else:
            total = total_info
        
        logger.info(f"ES搜索完成 - 查询: {query_params.q}, 结果数: {len(video_ids)}, 总数: {total}")
        
        # 提取高亮信息
        highlights = {}
        for hit in hits:
            video_id = hit["_source"]["id"]
            if "highlight" in hit:
                highlights[video_id] = hit["highlight"]
        
        if not video_ids:
            # 没有搜索结果，直接返回空列表
            return SearchResponse(
                videos=[],
                total=0,
                page=query_params.page,
                page_size=query_params.page_size,
                total_pages=0
            )
        
        # 4. 批量查询数据库获取完整信息（包括URL，使用 joinedload 预加载 author）
        from sqlalchemy.orm import joinedload
        stmt = select(Video).options(joinedload(Video.author)).where(Video.id.in_(video_ids))
        result = await db.execute(stmt)
        videos = result.scalars().all()
        
        # 5. 保持ES返回的顺序（重要！）
        video_dict = {v.id: v for v in videos}
        ordered_videos = [video_dict[vid] for vid in video_ids if vid in video_dict]
        
        # 6. 转换为响应格式
        video_responses = []
        for video in ordered_videos:
            # 获取作者名称
            author_name = None
            if video.author:
                author_name = video.author.user_name
            
            # 构建响应对象
            video_response = SearchVideoResponse(
                id=video.id,
                author_id=video.author_id,
                author_name=author_name,
                title=video.title or "",
                description=video.description,
                cover_url=video.cover_url,
                play_url=video.play_url,
                view_count=video.view_count or 0,
                favorite_count=video.favorite_count or 0,
                comment_count=video.comment_count or 0,
                publish_time=video.publish_time,
                highlight=highlights.get(video.id)
            )
            video_responses.append(video_response)
        
        # 7. 计算总页数
        total_pages = (total + query_params.page_size - 1) // query_params.page_size
        
        return SearchResponse(
            videos=video_responses,
            total=total,
            page=query_params.page,
            page_size=query_params.page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"ES搜索失败: {e}", exc_info=True)
        # 降级到数据库搜索
        return await _fallback_db_search(db, query_params)


async def _fallback_db_search(
    db: AsyncSession,
    query_params: SearchRequest
) -> SearchResponse:
    """
    降级到数据库搜索（当ES不可用时）
    
    Args:
        db: 数据库会话
        query_params: 搜索请求参数
        
    Returns:
        SearchResponse: 搜索结果
    """
    logger.warning("ES不可用，降级到数据库搜索")
    
    try:
        skip = (query_params.page - 1) * query_params.page_size
        
        # 构建查询（使用 joinedload 预加载 author 关联，避免异步懒加载问题）
        from sqlalchemy.orm import joinedload
        stmt = select(Video).options(joinedload(Video.author)).where(Video.status == "published")
        
        # 添加搜索条件
        if query_params.q:
            from sqlalchemy import or_
            search_term = f"%{query_params.q}%"
            stmt = stmt.where(
                or_(
                    Video.title.ilike(search_term),
                    Video.description.ilike(search_term)
                )
            )
        
        if query_params.author_id:
            stmt = stmt.where(Video.author_id == query_params.author_id)
        
        if query_params.video_id:
            stmt = stmt.where(Video.id == query_params.video_id)
        
        if query_params.start_time:
            stmt = stmt.where(Video.publish_time >= query_params.start_time)
        
        if query_params.end_time:
            stmt = stmt.where(Video.publish_time <= query_params.end_time)
        
        # 添加排序
        if query_params.sort == "time":
            stmt = stmt.order_by(Video.publish_time.desc())
        elif query_params.sort == "hot":
            # 数据库中没有hot_score，使用view_count + favorite_count作为替代
            from sqlalchemy import desc
            stmt = stmt.order_by(
                desc(Video.view_count + Video.favorite_count * 2)
            )
        else:
            stmt = stmt.order_by(Video.created_at.desc())
        
        # 执行查询
        result = await db.execute(stmt.offset(skip).limit(query_params.page_size))
        videos = result.scalars().all()
        
        # 获取总数
        count_stmt = select(Video).where(Video.status == "published")
        if query_params.q:
            from sqlalchemy import or_, func
            search_term = f"%{query_params.q}%"
            count_stmt = count_stmt.where(
                or_(
                    Video.title.ilike(search_term),
                    Video.description.ilike(search_term)
                )
            )
        total_result = await db.execute(select(func.count()).select_from(count_stmt.subquery()))
        total = total_result.scalar() or 0
        
        # 转换为响应格式
        video_responses = []
        for video in videos:
            author_name = None
            if video.author:
                author_name = video.author.user_name
            
            video_response = SearchVideoResponse(
                id=video.id,
                author_id=video.author_id,
                author_name=author_name,
                title=video.title or "",
                description=video.description,
                cover_url=video.cover_url,
                play_url=video.play_url,
                view_count=video.view_count or 0,
                favorite_count=video.favorite_count or 0,
                comment_count=video.comment_count or 0,
                publish_time=video.publish_time,
                highlight=None  # 数据库搜索不支持高亮
            )
            video_responses.append(video_response)
        
        total_pages = (total + query_params.page_size - 1) // query_params.page_size
        
        return SearchResponse(
            videos=video_responses,
            total=total,
            page=query_params.page,
            page_size=query_params.page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"数据库搜索失败: {e}", exc_info=True)
        return SearchResponse(
            videos=[],
            total=0,
            page=query_params.page,
            page_size=query_params.page_size,
            total_pages=0
        )

