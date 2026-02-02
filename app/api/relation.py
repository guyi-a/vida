"""
关注关系相关 API
提供关注、取消关注、查询关注列表和粉丝列表等功能
"""

from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.exception import NotFoundException, BadRequestException
from app.models.user import User
from app.crud import relation_crud, user_crud
from app.schemas.response.base_response import BaseResponse


router = APIRouter(prefix="/api/v1/relations", tags=["关注关系"])


def user_to_relation_info(user: User) -> dict:
    """
    将 User 模型转换为关系中的用户信息格式
    
    Args:
        user: User 模型对象
        
    Returns:
        dict: 用户信息字典
    """
    return {
        "id": user.id,
        "user_name": user.user_name,
        "avatar": user.avatar,
        "follow_count": user.follow_count,
        "follower_count": user.follower_count
    }


@router.post("/follow/{user_id}", response_model=BaseResponse, summary="关注用户")
async def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    关注用户
    
    - user_id: 要关注的用户ID
    - 需要登录
    - 不能关注自己
    - 不能重复关注
    - 关注数和粉丝数会自动更新（通过数据库 trigger）
    """
    try:
        # 检查是否关注自己
        if current_user.id == user_id:
            raise BadRequestException("不能关注自己")
        
        # 检查目标用户是否存在
        target_user = await user_crud.get_by_id(db, user_id)
        if not target_user:
            raise NotFoundException(f"用户不存在: {user_id}")
        
        # 检查是否已关注
        existing_relation = await relation_crud.get_relation(db, current_user.id, user_id)
        if existing_relation:
            raise BadRequestException(f"您已经关注过该用户了")
        
        # 创建关注关系
        relation = await relation_crud.create(db, current_user.id, user_id)
        
        # 重新获取用户信息以获取更新后的关注数和粉丝数
        follower_user = await user_crud.get_by_id(db, current_user.id)
        follow_user = await user_crud.get_by_id(db, user_id)
        
        # 提交事务
        await db.commit()
        
        return BaseResponse(
            success=True,
            message="关注成功",
            data={
                "follower_id": current_user.id,
                "follow_id": user_id,
                "created_at": relation.created_at.isoformat() if relation.created_at else None,
                "follow_count": follower_user.follow_count if follower_user else 0,
                "follower_count": follow_user.follower_count if follow_user else 0
            }
        )
        
    except (NotFoundException, BadRequestException):
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"关注失败: {str(e)}"
        )


@router.post("/unfollow/{user_id}", response_model=BaseResponse, summary="取消关注")
async def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消关注用户
    
    - user_id: 要取消关注的用户ID
    - 需要登录
    - 只能取消自己的关注
    - 关注数和粉丝数会自动更新（通过数据库 trigger）
    """
    try:
        # 检查是否已关注
        existing_relation = await relation_crud.get_relation(db, current_user.id, user_id)
        if not existing_relation:
            raise BadRequestException(f"您尚未关注该用户")
        
        # 取消关注
        success = await relation_crud.delete(db, current_user.id, user_id)
        
        if not success:
            raise BadRequestException(f"取消关注失败")
        
        # 重新获取用户信息以获取更新后的关注数和粉丝数
        follower_user = await user_crud.get_by_id(db, current_user.id)
        follow_user = await user_crud.get_by_id(db, user_id)
        
        # 提交事务
        await db.commit()
        
        from datetime import datetime
        return BaseResponse(
            success=True,
            message="取消关注成功",
            data={
                "follower_id": current_user.id,
                "follow_id": user_id,
                "unfollowed_at": datetime.utcnow().isoformat(),
                "follow_count": follower_user.follow_count if follower_user else 0,
                "follower_count": follow_user.follower_count if follow_user else 0
            }
        )
        
    except (NotFoundException, BadRequestException):
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"取消关注失败: {str(e)}"
        )


@router.get("/following/{user_id}", response_model=BaseResponse, summary="获取用户的关注列表")
async def get_user_following(
    user_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的关注列表
    
    - user_id: 用户ID
    - 需要登录
    - 返回该用户关注的所有用户
    - 支持分页查询
    """
    try:
        # 检查用户是否存在
        user = await user_crud.get_by_id(db, user_id)
        if not user:
            raise NotFoundException(f"用户不存在: {user_id}")
        
        skip = (page - 1) * page_size
        
        # 获取关注关系列表
        relations = await relation_crud.get_following_list(db, user_id, skip, page_size)
        
        # 提取被关注的用户ID
        follow_ids = [relation.follow_id for relation in relations]
        
        # 批量获取用户信息
        users = await user_crud.get_multiple_users(db, follow_ids)
        # 将用户列表转换为字典以便快速查找
        user_dict = {user.id: user for user in users}
        
        # 构建用户信息列表
        user_list = []
        for relation in relations:
            target_user = user_dict.get(relation.follow_id)
            if target_user:
                user_list.append(user_to_relation_info(target_user))
        
        # 获取总数
        total = await relation_crud.count_following(db, user_id)
        
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message="获取关注列表成功",
            data={
                "users": user_list,
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
            detail=f"获取关注列表失败: {str(e)}"
        )


@router.get("/followers/{user_id}", response_model=BaseResponse, summary="获取用户的粉丝列表")
async def get_user_followers(
    user_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的粉丝列表
    
    - user_id: 用户ID
    - 需要登录
    - 返回该用户的所有粉丝
    - 支持分页查询
    """
    try:
        # 检查用户是否存在
        user = await user_crud.get_by_id(db, user_id)
        if not user:
            raise NotFoundException(f"用户不存在: {user_id}")
        
        skip = (page - 1) * page_size
        
        # 获取粉丝关系列表
        relations = await relation_crud.get_follower_list(db, user_id, skip, page_size)
        
        # 提取粉丝用户ID
        follower_ids = [relation.follower_id for relation in relations]
        
        # 批量获取用户信息
        users = await user_crud.get_multiple_users(db, follower_ids)
        # 将用户列表转换为字典以便快速查找
        user_dict = {user.id: user for user in users}
        
        # 构建用户信息列表
        user_list = []
        for relation in relations:
            follower_user = user_dict.get(relation.follower_id)
            if follower_user:
                user_list.append(user_to_relation_info(follower_user))
        
        # 获取总数
        total = await relation_crud.count_followers(db, user_id)
        
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message="获取粉丝列表成功",
            data={
                "users": user_list,
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
            detail=f"获取粉丝列表失败: {str(e)}"
        )


@router.get("/following/{user_id}/status", response_model=BaseResponse, summary="查询关注状态")
async def get_follow_status(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查询当前用户对指定用户的关注状态
    
    - user_id: 目标用户ID
    - 需要登录
    - 返回是否已关注
    """
    try:
        # 检查目标用户是否存在
        target_user = await user_crud.get_by_id(db, user_id)
        if not target_user:
            raise NotFoundException(f"用户不存在: {user_id}")
        
        # 查询关注状态
        is_following = await relation_crud.is_following(db, current_user.id, user_id)
        
        return BaseResponse(
            success=True,
            message="查询关注状态成功",
            data={
                "is_following": is_following,
                "follow_id": user_id
            }
        )
        
    except NotFoundException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询关注状态失败: {str(e)}"
        )


@router.get("/following/my/list", response_model=BaseResponse, summary="获取我的关注列表")
async def get_my_following(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的关注列表
    
    - 需要登录
    - 返回当前用户关注的所有用户
    - 支持分页查询
    """
    try:
        skip = (page - 1) * page_size
        
        # 获取关注关系列表
        relations = await relation_crud.get_following_list(db, current_user.id, skip, page_size)
        
        # 提取被关注的用户ID
        follow_ids = [relation.follow_id for relation in relations]
        
        # 批量获取用户信息
        users = await user_crud.get_multiple_users(db, follow_ids)
        # 将用户列表转换为字典以便快速查找
        user_dict = {user.id: user for user in users}
        
        # 构建用户信息列表
        user_list = []
        for relation in relations:
            target_user = user_dict.get(relation.follow_id)
            if target_user:
                user_list.append(user_to_relation_info(target_user))
        
        # 获取总数
        total = await relation_crud.count_following(db, current_user.id)
        
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message="获取我的关注列表成功",
            data={
                "users": user_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取我的关注列表失败: {str(e)}"
        )


@router.get("/followers/my/list", response_model=BaseResponse, summary="获取我的粉丝列表")
async def get_my_followers(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的粉丝列表
    
    - 需要登录
    - 返回当前用户的所有粉丝
    - 支持分页查询
    """
    try:
        skip = (page - 1) * page_size
        
        # 获取粉丝关系列表
        relations = await relation_crud.get_follower_list(db, current_user.id, skip, page_size)
        
        # 提取粉丝用户ID
        follower_ids = [relation.follower_id for relation in relations]
        
        # 批量获取用户信息
        users = await user_crud.get_multiple_users(db, follower_ids)
        # 将用户列表转换为字典以便快速查找
        user_dict = {user.id: user for user in users}
        
        # 构建用户信息列表
        user_list = []
        for relation in relations:
            follower_user = user_dict.get(relation.follower_id)
            if follower_user:
                user_list.append(user_to_relation_info(follower_user))
        
        # 获取总数
        total = await relation_crud.count_followers(db, current_user.id)
        
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message="获取我的粉丝列表成功",
            data={
                "users": user_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取我的粉丝列表失败: {str(e)}"
        )


@router.post("/batch/status", response_model=BaseResponse, summary="批量查询关注状态")
async def get_batch_follow_status(
    user_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量查询当前用户对多个用户的关注状态
    
    - user_ids: 目标用户ID列表
    - 需要登录
    - 返回每个用户的关注状态
    """
    try:
        if not user_ids:
            raise BadRequestException("用户ID列表不能为空")
        
        if len(user_ids) > 100:
            raise BadRequestException("一次最多查询100个用户的关注状态")
        
        # 批量查询关注状态
        follow_status = await relation_crud.get_multiple_users_following_status(
            db, current_user.id, user_ids
        )
        
        return BaseResponse(
            success=True,
            message="批量查询关注状态成功",
            data={
                "follow_status": follow_status
            }
        )
        
    except BadRequestException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"批量查询关注状态失败: {str(e)}"
        )


@router.get("/mutual", response_model=BaseResponse, summary="获取互相关注列表")
async def get_mutual_followers(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的互相关注列表
    
    - 需要登录
    - 返回与当前用户互相关注的用户
    - 支持分页查询
    """
    try:
        skip = (page - 1) * page_size
        
        # 获取互相关注的关系
        mutual_relations = await relation_crud.get_mutual_followers(
            db, current_user.id, skip, page_size
        )
        
        # 提取互相关注的用户ID
        mutual_user_ids = [relation["user_id"] for relation in mutual_relations]
        
        # 批量获取用户信息
        users = await user_crud.get_multiple_users(db, mutual_user_ids)
        # 将用户列表转换为字典以便快速查找
        user_dict = {user.id: user for user in users}
        
        # 构建用户信息列表
        user_list = []
        for relation in mutual_relations:
            target_user = user_dict.get(relation["user_id"])
            if target_user:
                user_info = user_to_relation_info(target_user)
                user_info["relation_type"] = relation["relation_type"]
                user_list.append(user_info)
        
        # 获取总数
        total = await relation_crud.count_mutual_followers(db, current_user.id)
        
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message="获取互相关注列表成功",
            data={
                "users": user_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取互相关注列表失败: {str(e)}"
        )
