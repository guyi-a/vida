from pydantic import BaseModel, Field
from typing import Optional


class UserUpdateRequest(BaseModel):
    """
    用户更新请求模型
    """
    username: Optional[str] = Field(
        None,
        description="用户名",
        example="新用户名",
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
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "新用户名",
                "avatar": "https://example.com/avatar.jpg",
                "background_image": "https://example.com/background.jpg"
            }
        }