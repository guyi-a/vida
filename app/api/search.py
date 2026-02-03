"""
搜索相关 API
提供视频搜索功能
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.schemas.request.search_request import SearchRequest
from app.schemas.response.base_response import BaseResponse
from app.schemas.response.search_response import SearchResponse
from app.crud import search_crud

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

