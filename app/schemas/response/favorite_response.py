"""
点赞相关响应模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FavoriteInfoResponse(BaseModel):
    """
    点赞信息响应模型
    """
    id: int = Field(..., description="点赞记录ID")
    user_id: int = Field(..., description="用户ID")
    video_id: int = Field(..., description="视频ID")
    created_at: str = Field(..., description="点赞时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 123,
                "video_id": 456,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class FavoriteCreateResponse(BaseModel):
    """
    点赞操作响应模型
    """
    favorite_id: int = Field(..., description="点赞记录ID")
    user_id: int = Field(..., description="用户ID")
    video_id: int = Field(..., description="视频ID")
    created_at: str = Field(..., description="点赞时间")
    total_favorites: int = Field(..., description="视频当前总点赞数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "favorite_id": 1,
                "user_id": 123,
                "video_id": 456,
                "created_at": "2024-01-01T12:00:00Z",
                "total_favorites": 10
            }
        }


class FavoriteDeleteResponse(BaseModel):
    """
    取消点赞响应模型
    """
    favorite_id: Optional[int] = Field(None, description="已删除的点赞记录ID（如果有）")
    user_id: int = Field(..., description="用户ID")
    video_id: int = Field(..., description="视频ID")
    total_favorites: int = Field(..., description="视频当前总点赞数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "favorite_id": 1,
                "user_id": 123,
                "video_id": 456,
                "total_favorites": 9
            }
        }


class FavoriteStatusResponse(BaseModel):
    """
    点赞状态响应模型
    """
    is_favorited: bool = Field(..., description="是否已点赞")
    video_id: int = Field(..., description="视频ID")
    total_favorites: int = Field(..., description="视频总点赞数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_favorited": True,
                "video_id": 456,
                "total_favorites": 10
            }
        }


class FavoriteListResponse(BaseModel):
    """
    点赞列表响应模型
    """
    favorites: List[FavoriteInfoResponse] = Field(..., description="点赞记录列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "favorites": [
                    {
                        "id": 1,
                        "user_id": 123,
                        "video_id": 456,
                        "created_at": "2024-01-01T12:00:00Z"
                    }
                ],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }


class BatchFavoriteStatusResponse(BaseModel):
    """
    批量点赞状态响应模型
    """
    favorites_status: dict = Field(..., description="视频ID到点赞状态的映射")
    
    class Config:
        json_schema_extra = {
            "example": {
                "favorites_status": {
                    "456": True,
                    "457": False,
                    "458": True
                }
            }
        }
