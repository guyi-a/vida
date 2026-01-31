from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class TokenResponse(BaseModel):
    """
    Token响应模型
    """
    access_token: str = Field(
        ..., 
        description="访问令牌",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    token_type: str = Field(
        "bearer", 
        description="令牌类型",
        example="bearer"
    )
    expires_in: int = Field(
        240, 
        description="过期时间（分钟）",
        example=240
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 240
            }
        }


class UserInfoResponse(BaseModel):
    """
    用户信息响应模型
    """
    id: int = Field(
        ..., 
        description="用户ID",
        example=1
    )
    username: str = Field(
        ..., 
        description="用户名",
        example="testuser"
    )
    avatar: Optional[str] = Field(
        None, 
        description="用户头像URL",
        example="https://example.com/avatar.jpg"
    )
    background_image: Optional[str] = Field(
        None, 
        description="背景图片URL",
        example="https://example.com/background.jpg"
    )
    userRole: str = Field(
        ..., 
        description="用户角色",
        example="user"
    )
    follow_count: int = Field(
        0, 
        description="关注数量",
        example=0
    )
    follower_count: int = Field(
        0, 
        description="粉丝数量",
        example=0
    )
    total_favorited: int = Field(
        0, 
        description="被点赞总数",
        example=0
    )
    favorite_count: int = Field(
        0, 
        description="点赞数量",
        example=0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "testuser",
                "avatar": "https://example.com/avatar.jpg",
                "background_image": "https://example.com/background.jpg",
                "userRole": "user",
                "follow_count": 0,
                "follower_count": 0,
                "total_favorited": 0,
                "favorite_count": 0
            }
        }


class LoginResponse(BaseModel):
    """
    登录响应模型
    """
    success: bool = Field(
        True, 
        description="登录是否成功"
    )
    message: str = Field(
        "登录成功", 
        description="响应消息"
    )
    data: Dict[str, Any] = Field(
        ..., 
        description="登录数据，包含token和用户信息"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "登录成功",
                "data": {
                    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 240,
                    "user": {
                        "id": 1,
                        "username": "testuser",
                        "avatar": "https://example.com/avatar.jpg",
                        "userRole": "user"
                    }
                }
            }
        }


class RegisterResponse(BaseModel):
    """
    注册响应模型
    """
    success: bool = Field(
        True, 
        description="注册是否成功"
    )
    message: str = Field(
        "注册成功", 
        description="响应消息"
    )
    data: Optional[UserInfoResponse] = Field(
        None, 
        description="注册后的用户信息"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "注册成功",
                "data": {
                    "id": 1,
                    "username": "testuser",
                    "avatar": "https://example.com/avatar.jpg",
                    "userRole": "user",
                    "follow_count": 0,
                    "follower_count": 0,
                    "total_favorited": 0,
                    "favorite_count": 0
                }
            }
        }


class LogoutResponse(BaseModel):
    """
    登出响应模型
    """
    success: bool = Field(
        True, 
        description="登出是否成功"
    )
    message: str = Field(
        "登出成功", 
        description="响应消息"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "登出成功"
            }
        }