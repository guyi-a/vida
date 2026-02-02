"""
点赞相关 API
提供点赞、取消点赞、查询点赞状态等功能
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.exception import NotFoundException, BadRequestException
from app.core.config import settings
from app.models.user import User
from app.crud import favorite_crud, video_crud
from app.schemas.response.base_response import BaseResponse
from app.schemas.response.favorite_response import (
    FavoriteInfoResponse,
    FavoriteCreateResponse,
    FavoriteDeleteResponse,
    FavoriteStatusResponse,
    FavoriteListResponse
)


router = APIRouter(prefix="/api/v1/favorites", tags=["点赞管理"])


def favorite_to_response(favorite) -> dict:
    """
    将 Favorite 模型转换为响应格式
    
    Args:
        favorite: Favorite 模型对象
        
    Returns:
        dict: 点赞信息字典
    """
    return {
        "id": favorite.id,
        "user_id": favorite.user_id,
        "video_id": favorite.video_id,
        "created_at": favorite.created_at.isoformat() if favorite.created_at else None
    }


@router.post("/{video_id}", response_model=BaseResponse, summary="点赞视频")
async def favorite_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    点赞视频
    
    - video_id: 视频ID
    - 需要登录
    - 同一用户对同一视频只能点赞一次
    - 点赞成功后会返回视频的总点赞数
    """
    try:
        # 检查视频是否存在
        video = await video_crud.get_by_id(db, video_id)
        if not video:
            raise NotFoundException(f"视频不存在: {video_id}")
        
        # 检查是否已经点赞
        existing_favorite = await favorite_crud.get_by_user_and_video(
            db, current_user.id, video_id
        )
        if existing_favorite:
            raise BadRequestException(f"您已经点赞过该视频了")
        
        # 创建点赞记录
        favorite = await favorite_crud.create(db, current_user.id, video_id)
        
        # 更新视频的点赞数
        await video_crud.increment_favorite_count(db, video_id)
        
        # 获取更新后的总点赞数
        updated_video = await video_crud.get_by_id(db, video_id)
        total_favorites = updated_video.favorite_count if updated_video else 0
        
        # 提交事务
        await db.commit()
        
        return BaseResponse(
            success=True,
            message="点赞成功",
            data={
                "favorite_id": favorite.id,
                "user_id": current_user.id,
                "video_id": video_id,
                "created_at": favorite.created_at.isoformat() if favorite.created_at else None,
                "total_favorites": total_favorites
            }
        )
        
    except (NotFoundException, BadRequestException):
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"点赞失败: {str(e)}"
        )


@router.delete("/{video_id}", response_model=BaseResponse, summary="取消点赞")
async def unfavorite_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消点赞视频
    
    - video_id: 视频ID
    - 需要登录
    - 只能取消自己的点赞
    """
    try:
        # 检查是否已点赞
        existing_favorite = await favorite_crud.get_by_user_and_video(
            db, current_user.id, video_id
        )
        if not existing_favorite:
            raise BadRequestException(f"您尚未点赞该视频")
        
        # 取消点赞
        success = await favorite_crud.delete(db, current_user.id, video_id)
        
        if not success:
            raise BadRequestException(f"取消点赞失败")
        
        # 更新视频的点赞数
        await video_crud.decrement_favorite_count(db, video_id)
        
        # 获取更新后的总点赞数
        updated_video = await video_crud.get_by_id(db, video_id)
        total_favorites = updated_video.favorite_count if updated_video else 0
        
        # 提交事务
        await db.commit()
        
        return BaseResponse(
            success=True,
            message="取消点赞成功",
            data={
                "favorite_id": existing_favorite.id,
                "user_id": current_user.id,
                "video_id": video_id,
                "total_favorites": total_favorites
            }
        )
        
    except (NotFoundException, BadRequestException):
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"取消点赞失败: {str(e)}"
        )


@router.get("/{video_id}/status", response_model=BaseResponse, summary="查询点赞状态")
async def get_favorite_status(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查询当前用户对视频的点赞状态
    
    - video_id: 视频ID
    - 需要登录
    - 返回是否已点赞和视频总点赞数
    """
    try:
        # 检查视频是否存在
        video = await video_crud.get_by_id(db, video_id)
        if not video:
            raise NotFoundException(f"视频不存在: {video_id}")
        
        # 查询点赞状态
        is_favorited = await favorite_crud.is_favorited(
            db, current_user.id, video_id
        )
        
        # 获取总点赞数
        total_favorites = await favorite_crud.count_by_video(db, video_id)
        
        return BaseResponse(
            success=True,
            message="查询点赞状态成功",
            data={
                "is_favorited": is_favorited,
                "video_id": video_id,
                "total_favorites": total_favorites
            }
        )
        
    except NotFoundException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询点赞状态失败: {str(e)}"
        )


@router.get("/my/list", response_model=BaseResponse, summary="获取我的点赞列表")
async def get_my_favorites(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的点赞列表
    
    - 需要登录
    - 返回用户点赞过的视频列表
    - 支持分页查询
    """
    try:
        skip = (page - 1) * page_size
        
        # 获取点赞记录
        favorites = await favorite_crud.get_by_user(
            db, current_user.id, skip, page_size
        )
        
        # 获取总数
        total = await favorite_crud.count_by_user(db, current_user.id)
        
        # 转换为响应格式
        favorite_list = [favorite_to_response(fav) for fav in favorites]
        
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message="获取我的点赞列表成功",
            data={
                "favorites": favorite_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取我的点赞列表失败: {str(e)}"
        )


@router.get("/video/{video_id}/list", response_model=BaseResponse, summary="获取视频的点赞列表")
async def get_video_favorites(
    video_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频的点赞用户列表
    
    - video_id: 视频ID
    - 需要登录
    - 返回点赞了该视频的用户列表
    - 支持分页查询
    """
    try:
        # 检查视频是否存在
        video = await video_crud.get_by_id(db, video_id)
        if not video:
            raise NotFoundException(f"视频不存在: {video_id}")
        
        skip = (page - 1) * page_size
        
        # 获取点赞记录
        favorites = await favorite_crud.get_by_video(
            db, video_id, skip, page_size
        )
        
        # 获取总数
        total = await favorite_crud.count_by_video(db, video_id)
        
        # 转换为响应格式
        favorite_list = [favorite_to_response(fav) for fav in favorites]
        
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message="获取视频点赞列表成功",
            data={
                "favorites": favorite_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        )
        
    except NotFoundException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取视频点赞列表失败: {str(e)}"
        )


@router.post("/batch/status", response_model=BaseResponse, summary="批量查询点赞状态")
async def get_batch_favorite_status(
    video_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量查询当前用户对多个视频的点赞状态
    
    - video_ids: 视频ID列表
    - 需要登录
    - 返回每个视频的点赞状态
    """
    try:
        if not video_ids:
            raise BadRequestException("视频ID列表不能为空")
        
        if len(video_ids) > 100:
            raise BadRequestException("一次最多查询100个视频的点赞状态")
        
        # 批量查询点赞状态
        favorites_status = await favorite_crud.get_multiple_videos_favorited_status(
            db, current_user.id, video_ids
        )
        
        return BaseResponse(
            success=True,
            message="批量查询点赞状态成功",
            data={
                "favorites_status": favorites_status
            }
        )
        
    except BadRequestException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"批量查询点赞状态失败: {str(e)}"
        )


@router.get("/my/videos", response_model=BaseResponse, summary="获取我点赞的视频ID列表")
async def get_my_favorited_videos(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户点赞的视频ID列表
    
    - 需要登录
    - 返回用户点赞过的视频ID列表
    - 用于前端批量获取视频详情
    - 支持分页查询
    """
    try:
        skip = (page - 1) * page_size
        
        # 获取点赞的视频ID列表
        video_ids = await favorite_crud.get_favorited_video_ids(
            db, current_user.id, skip, page_size
        )
        
        # 获取总数
        total = await favorite_crud.count_by_user(db, current_user.id)
        
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message="获取我点赞的视频ID列表成功",
            data={
                "video_ids": video_ids,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取我点赞的视频ID列表失败: {str(e)}"
        )
