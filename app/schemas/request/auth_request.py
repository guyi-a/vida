from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    """
    登录请求模型
    """
    username: str = Field(
        ..., 
        description="用户名",
        example="admin",
        min_length=1,
        max_length=255
    )
    password: str = Field(
        ..., 
        description="密码",
        example="password123",
        min_length=6,
        max_length=255
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "password123"
            }
        }


class RegisterRequest(BaseModel):
    """
    注册请求模型
    """
    username: str = Field(
        ..., 
        description="用户名",
        example="testuser",
        min_length=1,
        max_length=255
    )
    password: str = Field(
        ..., 
        description="密码",
        example="password123",
        min_length=6,
        max_length=255
    )
    avatar: Optional[str] = Field(
        None, 
        description="用户头像URL",
        example="https://example.com/avatar.jpg",
        max_length=500
    )
    background_image: Optional[str] = Field(
        None, 
        description="背景图片URL",
        example="https://example.com/background.jpg",
        max_length=500
    )
    userRole: Optional[str] = Field(
        "user", 
        description="用户角色：user/admin",
        example="user"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "testuser",
                "password": "password123",
                "avatar": "https://example.com/avatar.jpg",
                "background_image": "https://example.com/background.jpg",
                "userRole": "user"
            }
        }