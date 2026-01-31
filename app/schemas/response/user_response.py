from pydantic import BaseModel, Field
from typing import Optional, List
from .auth_response import UserInfoResponse


class UserListResponse(BaseModel):
    """
    用户列表响应模型
    """
    users: List[UserInfoResponse] = Field(
        ...,
        description="用户列表"
    )
    total: int = Field(
        ...,
        description="总用户数量",
        example=100
    )
    page: int = Field(
        ...,
        description="当前页码",
        example=1
    )
    page_size: int = Field(
        ...,
        description="每页数量",
        example=20
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "id": 1,
                        "username": "john_doe",
                        "avatar": "https://example.com/avatar.jpg",
                        "background_image": None,
                        "userRole": "user",
                        "follow_count": 10,
                        "follower_count": 25
                    }
                ],
                "total": 100,
                "page": 1,
                "page_size": 20
            }
        }


class UserUpdateResponse(BaseModel):
    """
    用户更新响应模型
    """
    user: UserInfoResponse = Field(
        ...,
        description="更新后的用户信息"
    )
    message: str = Field(
        default="用户信息更新成功",
        description="响应消息",
        example="用户信息更新成功"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": 1,
                    "username": "updated_username",
                    "avatar": "https://example.com/new_avatar.jpg",
                    "background_image": "https://example.com/new_background.jpg",
                    "userRole": "user",
                    "follow_count": 10,
                    "follower_count": 25
                },
                "message": "用户信息更新成功"
            }
        }


class PasswordChangeResponse(BaseModel):
    """
    密码修改响应模型
    """
    message: str = Field(
        default="密码修改成功",
        description="响应消息",
        example="密码修改成功"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "密码修改成功"
            }
        }


class UserDeleteResponse(BaseModel):
    """
    用户删除响应模型
    """
    message: str = Field(
        default="用户删除成功",
        description="响应消息",
        example="用户删除成功"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "用户删除成功"
            }
        }