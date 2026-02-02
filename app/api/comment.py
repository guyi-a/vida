"""
评论相关 API
提供发表评论、删除评论、查询评论等功能
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.exception import NotFoundException, BadRequestException
from app.models.user import User
from app.crud import comment_crud, video_crud
from app.schemas.response.base_response import BaseResponse
from app.schemas.request.comment_request import CommentCreateRequest, CommentUpdateRequest


router = APIRouter(prefix="/api/v1/comments", tags=["评论管理"])


def comment_to_response(comment, include_replies: bool = False) -> dict:
    """
    将 Comment 模型转换为响应格式
    
    Args:
        comment: Comment 模型对象
        include_replies: 是否包含回复信息
        
    Returns:
        dict: 评论信息字典
    """
    comment_dict = {
        "id": comment.id,
        "user_id": comment.user_id,
        "video_id": comment.video_id,
        "content": comment.content,
        "parent_id": comment.parent_id,
        "like_count": comment.like_count,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None
    }
    
    # 添加用户信息（如果已加载）
    # 使用getattr避免触发延迟加载
    user = getattr(comment, 'user', None)
    if user is not None:
        try:
            # 确保访问用户属性不会触发延迟加载
            # 如果user对象已经加载，直接访问属性
            if hasattr(user, 'user_name'):
                comment_dict["username"] = user.user_name
            else:
                comment_dict["username"] = getattr(user, 'user_name', None) or getattr(user, 'username', None)
            
            if hasattr(user, 'avatar'):
                comment_dict["avatar"] = user.avatar
            else:
                comment_dict["avatar"] = getattr(user, 'avatar', None)
        except Exception as e:
            # 如果访问失败，记录错误但使用默认值
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"访问评论 {comment.id} 的用户信息失败: {str(e)}")
            comment_dict["username"] = None
            comment_dict["avatar"] = None
    else:
        # 如果user关系未加载，设置为None
        comment_dict["username"] = None
        comment_dict["avatar"] = None
    
    # 注意：不要直接访问replies关系，这可能会触发延迟加载
    # replies_count应该通过count_replies方法获取，而不是从关系对象中获取
    # 只有在明确加载了replies关系时才访问
    if include_replies:
        replies = getattr(comment, 'replies', None)
        if replies is not None:
            try:
                # 只有在replies已经被加载的情况下才访问
                # 使用list()强制评估，避免延迟加载
                replies_list = list(replies) if hasattr(replies, '__iter__') else []
                comment_dict["replies_count"] = len(replies_list)
                comment_dict["replies"] = [
                    comment_to_response(reply, include_replies=False)
                    for reply in replies_list
                ]
            except Exception:
                # 如果访问失败，说明replies未加载，跳过
                pass
    
    return comment_dict


@router.post("/{video_id}", response_model=BaseResponse, summary="发表评论")
async def create_comment(
    video_id: int,
    request: CommentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发表评论
    
    - video_id: 视频ID
    - content: 评论内容
    - parent_id: 父评论ID（可选，用于回复）
    - 需要登录
    - 评论内容长度限制：1-1000 字符
    """
    try:
        # 检查视频是否存在
        video = await video_crud.get_by_id(db, video_id)
        if not video:
            raise NotFoundException(f"视频不存在: {video_id}")
        
        # 如果是回复评论，检查父评论是否存在
        if request.parent_id:
            parent_comment = await comment_crud.get_by_id(db, request.parent_id)
            if not parent_comment:
                raise NotFoundException(f"父评论不存在: {request.parent_id}")
            # 检查父评论是否属于同一视频
            if parent_comment.video_id != video_id:
                raise BadRequestException("父评论不属于该视频")
        
        # 创建评论
        comment = await comment_crud.create(
            db, 
            current_user.id, 
            video_id, 
            request.content,
            request.parent_id
        )
        
        # 更新视频的评论数
        await video_crud.increment_comment_count(db, video_id)
        
        # 提交事务
        await db.commit()
        
        return BaseResponse(
            success=True,
            message="发表评论成功",
            data={
                "comment_id": comment.id,
                "user_id": current_user.id,
                "video_id": video_id,
                "content": comment.content,
                "parent_id": comment.parent_id,
                "created_at": comment.created_at.isoformat() if comment.created_at else None
            }
        )
        
    except (NotFoundException, BadRequestException):
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"发表评论失败: {str(e)}"
        )


@router.put("/{comment_id}", response_model=BaseResponse, summary="更新评论")
async def update_comment(
    comment_id: int,
    request: CommentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新评论
    
    - comment_id: 评论ID
    - content: 新的评论内容
    - 需要登录
    - 只能更新自己的评论
    - 评论内容长度限制：1-1000 字符
    """
    try:
        # 更新评论
        updated_comment = await comment_crud.update(
            db, 
            comment_id, 
            current_user.id,
            request.content
        )
        
        if not updated_comment:
            raise NotFoundException(f"评论不存在或无权限修改: {comment_id}")
        
        # 提交事务
        await db.commit()
        
        return BaseResponse(
            success=True,
            message="更新评论成功",
            data={
                "comment_id": updated_comment.id,
                "content": updated_comment.content,
                "updated_at": updated_comment.updated_at.isoformat() if updated_comment.updated_at else None
            }
        )
        
    except NotFoundException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"更新评论失败: {str(e)}"
        )


@router.delete("/{comment_id}", response_model=BaseResponse, summary="删除评论")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除评论
    
    - comment_id: 评论ID
    - 需要登录
    - 只能删除自己的评论
    - 删除评论会同时删除其所有回复（通过数据库级联删除）
    """
    try:
        # 检查评论是否存在
        comment = await comment_crud.get_by_id(db, comment_id)
        if not comment:
            raise NotFoundException(f"评论不存在: {comment_id}")
        
        # 删除评论
        success = await comment_crud.delete(db, comment_id, current_user.id)
        
        if not success:
            raise BadRequestException(f"删除失败或无权限删除: {comment_id}")
        
        # 更新视频的评论数
        await video_crud.decrement_comment_count(db, comment.video_id)
        
        # 提交事务
        await db.commit()
        
        from datetime import datetime
        return BaseResponse(
            success=True,
            message="删除评论成功",
            data={
                "comment_id": comment_id,
                "deleted_at": datetime.utcnow().isoformat()
            }
        )
        
    except NotFoundException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"删除评论失败: {str(e)}"
        )


@router.get("/video/{video_id}", response_model=BaseResponse, summary="获取视频评论列表")
async def get_video_comments(
    video_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    parent_id: Optional[int] = Query(None, description="父评论ID（None表示获取顶级评论）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频的评论列表
    
    - video_id: 视频ID
    - parent_id: 父评论ID（可选，None表示获取顶级评论）
    - 需要登录
    - 支持分页查询
    - 包含用户基本信息
    """
    try:
        # 检查视频是否存在
        video = await video_crud.get_by_id(db, video_id)
        if not video:
            raise NotFoundException(f"视频不存在: {video_id}")
        
        skip = (page - 1) * page_size
        
        # 获取评论列表
        comments = await comment_crud.get_by_video(
            db, video_id, skip, page_size, parent_id, load_user=True
        )
        
        # 获取总数
        total = await comment_crud.count_by_video(db, video_id, parent_id)
        
        # 转换为响应格式
        # 注意：确保在访问comment对象属性之前，所有关联对象都已加载
        comment_list = []
        for comment in comments:
            # 确保用户信息已加载（通过joinedload已经加载，这里只是确保访问安全）
            try:
                # 获取回复数量
                replies_count = await comment_crud.count_replies(db, comment.id)
                comment_dict = comment_to_response(comment)
                comment_dict["replies_count"] = replies_count
                comment_list.append(comment_dict)
            except Exception as e:
                # 如果访问comment对象时出错，记录错误但继续处理其他评论
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"处理评论 {comment.id} 时出错: {str(e)}")
                # 创建一个基本的评论字典，不包含用户信息
                comment_dict = {
                    "id": comment.id,
                    "user_id": comment.user_id,
                    "video_id": comment.video_id,
                    "content": comment.content,
                    "parent_id": comment.parent_id,
                    "like_count": comment.like_count,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
                    "username": None,
                    "avatar": None,
                    "replies_count": 0
                }
                comment_list.append(comment_dict)
        
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message="获取评论列表成功",
            data={
                "comments": comment_list,
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
            detail=f"获取评论列表失败: {str(e)}"
        )


@router.get("/video/{video_id}/tree", response_model=BaseResponse, summary="获取视频评论树")
async def get_video_comments_tree(
    video_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频评论树形结构
    
    - video_id: 视频ID
    - 返回顶级评论及其直接回复（每条顶级评论最多3条回复）
    - 需要登录
    - 支持分页查询
    """
    try:
        # 检查视频是否存在
        video = await video_crud.get_by_id(db, video_id)
        if not video:
            raise NotFoundException(f"视频不存在: {video_id}")
        
        skip = (page - 1) * page_size
        
        # 获取评论树
        comments = await comment_crud.get_comments_tree(
            db, video_id, skip, page_size, load_user=True
        )
        
        # 获取总数（顶级评论数）
        total = await comment_crud.count_by_video(db, video_id, parent_id=None)
        
        # 转换为响应格式
        comment_list = []
        for comment in comments:
            # 获取所有回复数量
            all_replies_count = await comment_crud.count_replies(db, comment.id)
            comment_dict = comment_to_response(comment, include_replies=True)
            comment_dict["replies_count"] = all_replies_count
            comment_list.append(comment_dict)
        
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message="获取评论树成功",
            data={
                "comments": comment_list,
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
            detail=f"获取评论树失败: {str(e)}"
        )


@router.get("/{comment_id}/replies", response_model=BaseResponse, summary="获取评论的回复列表")
async def get_comment_replies(
    comment_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取评论的回复列表
    
    - comment_id: 父评论ID
    - 需要登录
    - 支持分页查询
    """
    try:
        # 检查评论是否存在
        parent_comment = await comment_crud.get_by_id(db, comment_id)
        if not parent_comment:
            raise NotFoundException(f"评论不存在: {comment_id}")
        
        skip = (page - 1) * page_size
        
        # 获取回复列表
        replies = await comment_crud.get_replies(db, comment_id, skip, page_size, load_user=True)
        
        # 获取总数
        total = await comment_crud.count_replies(db, comment_id)
        
        # 转换为响应格式
        reply_list = [comment_to_response(reply) for reply in replies]
        
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message="获取回复列表成功",
            data={
                "comments": reply_list,
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
            detail=f"获取回复列表失败: {str(e)}"
        )


@router.get("/my/list", response_model=BaseResponse, summary="获取我的评论列表")
async def get_my_comments(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的评论列表
    
    - 需要登录
    - 返回当前用户发表过的评论
    - 支持分页查询
    """
    try:
        skip = (page - 1) * page_size
        
        # 获取评论列表
        comments = await comment_crud.get_by_user(
            db, current_user.id, skip, page_size, load_video=True
        )
        
        # 获取总数
        total = await comment_crud.count_by_user(db, current_user.id)
        
        # 转换为响应格式
        comment_list = []
        for comment in comments:
            # 获取回复数量
            replies_count = await comment_crud.count_replies(db, comment.id)
            comment_dict = comment_to_response(comment)
            comment_dict["replies_count"] = replies_count
            
            # 添加视频标题
            if hasattr(comment, 'video') and comment.video:
                comment_dict["video_title"] = comment.video.title
            
            comment_list.append(comment_dict)
        
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message="获取我的评论列表成功",
            data={
                "comments": comment_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取我的评论列表失败: {str(e)}"
        )
