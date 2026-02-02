"""
关注关系相关响应模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class RelationInfoResponse(BaseModel):
    """
    关系信息响应模型
    """
    id: int = Field(..., description="关系ID")
    follower_id: int = Field(..., description="粉丝用户ID")
    follow_id: int = Field(..., description="被关注用户ID")
    created_at: str = Field(..., description="关注时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "follower_id": 123,
                "follow_id": 456,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class UserInfoInRelation(BaseModel):
    """
    关系中的用户信息响应模型
    """
    id: int = Field(..., description="用户ID")
    user_name: str = Field(..., description="用户名")
    avatar: Optional[str] = Field(None, description="头像")
    follow_count: int = Field(..., description="关注数")
    follower_count: int = Field(..., description="粉丝数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 456,
                "user_name": "张三",
                "avatar": "https://example.com/avatar.jpg",
                "follow_count": 100,
                "follower_count": 200
            }
        }


class RelationDetailResponse(BaseModel):
    """
    关系详情响应模型（包含用户信息）
    """
    relation_id: int = Field(..., description="关系ID")
    follower_id: int = Field(..., description="粉丝用户ID")
    follow_id: int = Field(..., description="被关注用户ID")
    created_at: str = Field(..., description="关注时间")
    
    # 可选的用户信息
    follower_info: Optional[UserInfoInRelation] = Field(None, description="粉丝用户信息")
    follow_info: Optional[UserInfoInRelation] = Field(None, description="被关注用户信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "relation_id": 1,
                "follower_id": 123,
                "follow_id": 456,
                "created_at": "2024-01-01T12:00:00Z",
                "follower_info": {
                    "id": 123,
                    "user_name": "李四",
                    "avatar": "https://example.com/avatar2.jpg",
                    "follow_count": 50,
                    "follower_count": 100
                },
                "follow_info": {
                    "id": 456,
                    "user_name": "张三",
                    "avatar": "https://example.com/avatar.jpg",
                    "follow_count": 100,
                    "follower_count": 200
                }
            }
        }


class FollowResponse(BaseModel):
    """
    关注操作响应模型
    """
    follower_id: int = Field(..., description="关注者ID")
    follow_id: int = Field(..., description="被关注者ID")
    created_at: str = Field(..., description="关注时间")
    follow_count: int = Field(..., description="关注者当前关注数")
    follower_count: int = Field(..., description="被关注者当前粉丝数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "follower_id": 123,
                "follow_id": 456,
                "created_at": "2024-01-01T12:00:00Z",
                "follow_count": 101,
                "follower_count": 201
            }
        }


class UnfollowResponse(BaseModel):
    """
    取消关注响应模型
    """
    follower_id: int = Field(..., description="关注者ID")
    follow_id: int = Field(..., description="被关注者ID")
    unfollowed_at: str = Field(..., description="取关时间")
    follow_count: int = Field(..., description="关注者当前关注数")
    follower_count: int = Field(..., description="被关注者当前粉丝数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "follower_id": 123,
                "follow_id": 456,
                "unfollowed_at": "2024-01-01T13:00:00Z",
                "follow_count": 100,
                "follower_count": 200
            }
        }


class FollowStatusResponse(BaseModel):
    """
    关注状态响应模型
    """
    is_following: bool = Field(..., description="是否已关注")
    follow_id: int = Field(..., description="被关注用户ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_following": True,
                "follow_id": 456
            }
        }


class RelationListResponse(BaseModel):
    """
    关系列表响应模型
    """
    users: List[UserInfoInRelation] = Field(..., description="用户列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "id": 456,
                        "user_name": "张三",
                        "avatar": "https://example.com/avatar.jpg",
                        "follow_count": 100,
                        "follower_count": 200
                    }
                ],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }


class BatchFollowStatusResponse(BaseModel):
    """
    批量关注状态响应模型
    """
    follow_status: dict = Field(..., description="用户ID到关注状态的映射")
    
    class Config:
        json_schema_extra = {
            "example": {
                "follow_status": {
                    "456": True,
                    "457": False,
                    "458": True
                }
            }
        }


class MutualFollowResponse(BaseModel):
    """
    互相关注响应模型
    """
    users: List[UserInfoInRelation] = Field(..., description="互相关注的用户列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "id": 456,
                        "user_name": "张三",
                        "avatar": "https://example.com/avatar.jpg",
                        "follow_count": 100,
                        "follower_count": 200
                    }
                ],
                "total": 10,
                "page": 1,
                "page_size": 20,
                "total_pages": 1
            }
        }
