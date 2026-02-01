from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.core.dependencies import get_db, get_current_user, require_admin, check_owner_or_admin
from app.core.exception import NotFoundException, BadRequestException
from app.models.user import User
from app.crud import user_crud
from app.schemas.response.base_response import BaseResponse, PaginatedResponse
from app.schemas.response.user_response import UserListResponse, UserInfoResponse
from app.schemas.request.user_request import UserUpdateRequest


router = APIRouter(prefix="/api/v1/users", tags=["用户管理"])


@router.get("/me", response_model=BaseResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户的信息
    
    需要登录后才能调用。
    """
    user_info = {
        "id": current_user.id,
        "username": current_user.user_name,
        "avatar": current_user.avatar,
        "background_image": current_user.background_image,
        "userRole": current_user.userRole,
        "follow_count": current_user.follow_count,
        "follower_count": current_user.follower_count,
        "total_favorited": current_user.total_favorited,
        "favorite_count": current_user.favorite_count
    }
    
    return BaseResponse(
        success=True,
        message="获取成功",
        data=user_info
    )


@router.get("", response_model=PaginatedResponse, summary="获取用户列表")
async def get_users(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制"),
    username: Optional[str] = Query(None, description="用户名筛选（模糊匹配）"),
    user_role: Optional[str] = Query(None, description="用户角色筛选"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户列表
    
    需要管理员权限。
    
    - **skip**: 跳过数量（用于分页）
    - **limit**: 返回数量限制（1-100）
    - **username**: 用户名筛选（可选，模糊匹配）
    - **user_role**: 用户角色筛选（可选）
    """
    
    # 使用CRUD方法获取用户列表和总数
    users = await user_crud.get_users_with_filters(
        db=db,
        skip=skip,
        limit=limit,
        username=username,
        user_role=user_role
    )
    
    total = await user_crud.count_users_with_filters(
        db=db,
        username=username,
        user_role=user_role
    )
    
    # 转换为响应格式
    user_list = []
    for user in users:
        user_info = {
            "id": user.id,
            "username": user.user_name,
            "avatar": user.avatar,
            "background_image": user.background_image,
            "userRole": user.userRole,
            "follow_count": user.follow_count,
            "follower_count": user.follower_count,
            "total_favorited": user.total_favorited,
            "favorite_count": user.favorite_count
        }
        user_list.append(user_info)
    
    return PaginatedResponse(
        success=True,
        message="获取成功",
        data=user_list,
        meta={
            "page": skip // limit + 1,
            "page_size": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0
        }
    )


@router.get("/{user_id}", response_model=BaseResponse, summary="获取单个用户信息")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个用户信息
    
    本人或管理员可以查看。
    
    - **user_id**: 用户ID
    """
    # 检查权限：本人或管理员
    check_owner_or_admin(user_id, current_user)
    
    # 查询用户
    user = await user_crud.get_by_id(db, user_id)
    if not user:
        raise NotFoundException("用户不存在")
    
    user_info = {
        "id": user.id,
        "username": user.user_name,
        "avatar": user.avatar,
        "background_image": user.background_image,
        "userRole": user.userRole,
        "follow_count": user.follow_count,
        "follower_count": user.follower_count,
        "total_favorited": user.total_favorited,
        "favorite_count": user.favorite_count
    }
    
    return BaseResponse(
        success=True,
        message="获取成功",
        data=user_info
    )


@router.put("/{user_id}", response_model=BaseResponse, summary="更新用户信息")
async def update_user(
    user_id: int,
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户信息
    
    本人或管理员可以更新。
    
    - **user_id**: 用户ID
    """
    # 检查权限：本人或管理员
    check_owner_or_admin(user_id, current_user)
    
    # 准备更新数据
    update_dict = {}
    if update_data.username is not None:
        update_dict["user_name"] = update_data.username
    if update_data.avatar is not None:
        update_dict["avatar"] = update_data.avatar
    if update_data.background_image is not None:
        update_dict["background_image"] = update_data.background_image
    
    # 更新用户信息
    updated_user = await user_crud.update(db, user_id, update_dict)
    if not updated_user:
        raise NotFoundException("用户不存在")
    
    user_info = {
        "id": updated_user.id,
        "username": updated_user.user_name,
        "avatar": updated_user.avatar,
        "background_image": updated_user.background_image,
        "userRole": updated_user.userRole,
        "follow_count": updated_user.follow_count,
        "follower_count": updated_user.follower_count,
        "total_favorited": updated_user.total_favorited,
        "favorite_count": updated_user.favorite_count
    }
    
    return BaseResponse(
        success=True,
        message="更新成功",
        data=user_info
    )


@router.delete("/{user_id}", response_model=BaseResponse, summary="删除用户")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    删除用户（软删除）
    
    需要管理员权限。
    
    - **user_id**: 用户ID
    """
    # 检查用户是否存在
    user = await user_crud.get_by_id(db, user_id)
    if not user:
        raise NotFoundException("用户不存在")
    
    # 执行软删除（设置isDelete = 1）
    success = await user_crud.update(db, user_id, {"isDelete": 1})
    if not success:
        raise NotFoundException("用户不存在")
    
    return BaseResponse(
        success=True,
        message="删除成功"
    )


@router.post("/{user_id}/restore", response_model=BaseResponse, summary="恢复用户")
async def restore_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    恢复已删除的用户
    
    需要管理员权限。
    
    - **user_id**: 用户ID
    """
    # 检查用户是否存在
    user = await user_crud.get_by_id(db, user_id)
    if not user:
        raise NotFoundException("用户不存在")
    
    # 恢复用户（设置isDelete = 0）
    success = await user_crud.update(db, user_id, {"isDelete": 0})
    if not success:
        raise NotFoundException("用户不存在")
    
    return BaseResponse(
        success=True,
        message="恢复成功"
    )


@router.post("/{user_id}/set-admin", response_model=BaseResponse, summary="设置管理员角色")
async def set_admin_role(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    设置用户为管理员角色
    
    需要管理员权限。
    
    - **user_id**: 用户ID
    """
    # 检查用户是否存在
    user = await user_crud.get_by_id(db, user_id)
    if not user:
        raise NotFoundException("用户不存在")
    
    # 设置管理员角色
    updated_user = await user_crud.update(db, user_id, {"userRole": "admin"})
    if not updated_user:
        raise NotFoundException("用户不存在")
    
    return BaseResponse(
        success=True,
        message="设置管理员角色成功",
        data={
            "id": updated_user.id,
            "username": updated_user.user_name,
            "userRole": updated_user.userRole
        }
    )