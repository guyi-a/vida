from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.core.dependencies import get_db, get_current_user
from app.core.exception import UnauthorizedException, BadRequestException
from app.models.user import User
from app.crud.user_crud import user_crud
from app.utils.security import verify_password, get_password_hash, create_access_token
from app.schemas.request.auth_request import LoginRequest, RegisterRequest
from app.schemas.response.auth_response import LoginResponse, RegisterResponse, LogoutResponse


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse, status_code=200)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    用户登录
    
    Args:
        request: 登录请求数据
        db: 数据库会话
        
    Returns:
        LoginResponse: 登录响应，包含token和用户信息
        
    Raises:
        UnauthorizedException: 用户名或密码错误
    """
    # 查找用户
    user = await user_crud.get_by_username(db, request.username)
    if not user:
        raise UnauthorizedException("用户名或密码错误")
    
    # 验证密码（注意：这里使用简化的密码验证，实际生产环境应该使用hash验证）
    if not verify_password(request.password, user.password):
        raise UnauthorizedException("用户名或密码错误")
    
    # 检查用户是否被删除
    if user.isDelete != 0:
        raise UnauthorizedException("用户已被删除")
    
    # 生成token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # 转换为响应模型
    user_info = {
        "id": user.id,
        "username": user.user_name,
        "avatar": user.avatar,
        "background_image": user.background_image,
        "userRole": user.userRole,
        "follow_count": user.follow_count,
        "follower_count": user.follower_count
    }
    
    return LoginResponse(
        success=True,
        message="登录成功",
        data={
            "token": access_token,
            "token_type": "bearer",
            "expires_in": 14400,  # 4小时
            "user": user_info
        }
    )


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    用户注册
    
    Args:
        request: 注册请求数据
        db: 数据库会话
        
    Returns:
        RegisterResponse: 注册响应，包含用户信息
        
    Raises:
        BadRequestException: 用户名已存在或密码不匹配
    """
    # 检查用户名是否已存在
    existing_user = await user_crud.get_by_username(db, request.username)
    if existing_user:
        raise BadRequestException("用户名已存在")
    
    # 密码验证在这里可以添加额外的复杂度检查
    
    # 密码加密（注意：这里应该使用哈希）
    hashed_password = get_password_hash(request.password)
    
    # 创建用户数据
    user_data = {
        "user_name": request.username,
        "password": hashed_password,
        "avatar": request.avatar
    }
    
    # 创建用户
    user = await user_crud.create(db, user_data)
    
    # 转换为响应模型
    user_info = {
        "id": user.id,
        "username": user.user_name,
        "avatar": user.avatar,
        "background_image": user.background_image,
        "userRole": user.userRole,
        "follow_count": user.follow_count,
        "follower_count": user.follower_count
    }
    
    return RegisterResponse(
        user=user_info,
        message="注册成功"
    )


@router.post("/logout", response_model=LogoutResponse, status_code=200)
async def logout():
    """
    用户登出
    
    Returns:
        LogoutResponse: 登出响应
    """
    # 在实际应用中，这里可能需要：
    # 1. 将token加入黑名单
    # 2. 清除用户的会话
    # 3. 记录登出日志
    
    return LogoutResponse(
        message="登出成功"
    )


@router.get("/me", response_model=dict, status_code=200)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前用户（通过认证依赖获取）
        
    Returns:
        dict: 用户信息
    """
    return {
        "id": current_user.id,
        "username": current_user.user_name,
        "avatar": current_user.avatar,
        "background_image": current_user.background_image,
        "userRole": current_user.userRole,
        "follow_count": current_user.follow_count,
        "follower_count": current_user.follower_count
    }