"""
搜索相关 API
提供视频搜索功能
"""
import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_db, require_admin
from app.schemas.request.search_request import SearchRequest
from app.schemas.response.base_response import BaseResponse
from app.schemas.response.search_response import SearchResponse
from app.crud import search_crud
from app.models.video import Video
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/search", tags=["搜索"])


@router.get("/videos", response_model=BaseResponse, summary="搜索视频")
async def search_videos(
    q: str = Query(None, description="搜索关键词（标题/描述）"),
    author_id: int = Query(None, description="作者ID"),
    video_id: int = Query(None, description="视频ID（精确匹配）"),
    sort: str = Query("relevance", description="排序方式：relevance/time/hot"),
    start_time: int = Query(None, description="开始时间（Unix时间戳）"),
    end_time: int = Query(None, description="结束时间（Unix时间戳）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    搜索视频
    
    支持功能：
    - 全文搜索：标题和描述的全文检索
    - 结构化匹配：作者ID、视频ID的精确匹配
    - 时间范围：按发布时间过滤
    - 多种排序：相关性、时间、热度
    
    注意：
    - URL字段（play_url、cover_url）从数据库获取，不在ES中存储
    - 如果ES不可用，会自动降级到数据库搜索
    """
    try:
        # 构建搜索请求
        search_request = SearchRequest(
            q=q,
            author_id=author_id,
            video_id=video_id,
            sort=sort,
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size
        )
        
        # 执行搜索
        result = await search_crud.search_videos(db, search_request)
        
        return BaseResponse(
            success=True,
            message="搜索成功",
            data=result.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )


@router.post("/sync", response_model=BaseResponse, summary="同步视频到ES")
async def sync_videos_to_es(
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(require_admin)  # 可选：仅管理员可操作
):
    """
    手动同步所有已发布的视频到Elasticsearch
    
    用于：
    - 首次部署时初始化ES索引数据
    - ES数据丢失后重建索引
    - 数据不一致时修复
    """
    try:
        from app.infra.elasticsearch.sync_service import bulk_sync_videos_to_es
        
        # 获取所有已发布的视频
        stmt = select(Video).where(Video.status == "published")
        result = await db.execute(stmt)
        videos = result.scalars().all()
        
        if not videos:
            return BaseResponse(
                success=True,
                message="没有需要同步的视频",
                data={"synced": 0, "failed": 0}
            )
        
        # 获取作者信息
        author_ids = list(set(v.author_id for v in videos))
        author_stmt = select(User).where(User.id.in_(author_ids))
        author_result = await db.execute(author_stmt)
        authors = author_result.scalars().all()
        author_names = {a.id: a.user_name for a in authors}
        
        # 批量同步
        sync_result = await bulk_sync_videos_to_es(videos, author_names)
        
        logger.info(f"手动同步完成: 成功 {sync_result['success']} 个，失败 {sync_result['failed']} 个")
        
        return BaseResponse(
            success=True,
            message=f"同步完成：成功 {sync_result['success']} 个，失败 {sync_result['failed']} 个",
            data=sync_result
        )
        
    except Exception as e:
        logger.error(f"同步视频到ES失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"同步失败: {str(e)}"
        )

