"""
评论相关响应模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class CommentInfoResponse(BaseModel):
    """
    评论信息响应模型
    """
    id: int = Field(..., description="评论ID")
    user_id: int = Field(..., description="用户ID")
    video_id: int = Field(..., description="视频ID")
    content: str = Field(..., description="评论内容")
    parent_id: Optional[int] = Field(None, description="父评论ID")
    like_count: int = Field(..., description="点赞数")
    created_at: str = Field(..., description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    
    # 可选的关联信息
    username: Optional[str] = Field(None, description="用户名")
    avatar: Optional[str] = Field(None, description="用户头像")
    replies_count: Optional[int] = Field(0, description="回复数量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 123,
                "video_id": 456,
                "content": "这个视频很棒！",
                "parent_id": None,
                "like_count": 5,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": None,
                "username": "张三",
                "avatar": "https://example.com/avatar.jpg",
                "replies_count": 2
            }
        }


class CommentCreateResponse(BaseModel):
    """
    创建评论响应模型
    """
    comment_id: int = Field(..., description="评论ID")
    user_id: int = Field(..., description="用户ID")
    video_id: int = Field(..., description="视频ID")
    content: str = Field(..., description="评论内容")
    parent_id: Optional[int] = Field(None, description="父评论ID")
    created_at: str = Field(..., description="创建时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "comment_id": 1,
                "user_id": 123,
                "video_id": 456,
                "content": "这个视频很棒！",
                "parent_id": None,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class CommentUpdateResponse(BaseModel):
    """
    更新评论响应模型
    """
    comment_id: int = Field(..., description="评论ID")
    content: str = Field(..., description="更新后的内容")
    updated_at: str = Field(..., description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "comment_id": 1,
                "content": "更新后的评论内容",
                "updated_at": "2024-01-01T13:00:00Z"
            }
        }


class CommentDeleteResponse(BaseModel):
    """
    删除评论响应模型
    """
    comment_id: int = Field(..., description="已删除的评论ID")
    deleted_at: str = Field(..., description="删除时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "comment_id": 1,
                "deleted_at": "2024-01-01T14:00:00Z"
            }
        }


class CommentListResponse(BaseModel):
    """
    评论列表响应模型
    """
    comments: List[CommentInfoResponse] = Field(..., description="评论列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "comments": [
                    {
                        "id": 1,
                        "user_id": 123,
                        "video_id": 456,
                        "content": "这个视频很棒！",
                        "parent_id": None,
                        "like_count": 5,
                        "created_at": "2024-01-01T12:00:00Z",
                        "updated_at": None,
                        "username": "张三",
                        "avatar": "https://example.com/avatar.jpg",
                        "replies_count": 2
                    }
                ],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }


class CommentWithRepliesResponse(CommentInfoResponse):
    """
    带回复的评论响应模型
    """
    replies: List["CommentInfoResponse"] = Field(default_factory=list, description="回复列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 123,
                "video_id": 456,
                "content": "这个视频很棒！",
                "parent_id": None,
                "like_count": 5,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": None,
                "username": "张三",
                "avatar": "https://example.com/avatar.jpg",
                "replies_count": 2,
                "replies": [
                    {
                        "id": 2,
                        "user_id": 124,
                        "video_id": 456,
                        "content": "我也觉得！",
                        "parent_id": 1,
                        "like_count": 2,
                        "created_at": "2024-01-01T12:30:00Z",
                        "updated_at": None,
                        "username": "李四",
                        "avatar": "https://example.com/avatar2.jpg",
                        "replies_count": 0
                    }
                ]
            }
        }


# 更新前向引用，使 CommentWithRepliesResponse 能正确使用 CommentInfoResponse
CommentWithRepliesResponse.model_rebuild()


class CommentTreeResponse(BaseModel):
    """
    评论树形结构响应模型
    """
    comments: List[CommentWithRepliesResponse] = Field(..., description="评论树（包含回复）")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "comments": [
                    {
                        "id": 1,
                        "user_id": 123,
                        "video_id": 456,
                        "content": "这个视频很棒！",
                        "parent_id": None,
                        "like_count": 5,
                        "created_at": "2024-01-01T12:00:00Z",
                        "updated_at": None,
                        "username": "张三",
                        "avatar": "https://example.com/avatar.jpg",
                        "replies_count": 2,
                        "replies": [
                            {
                                "id": 2,
                                "user_id": 124,
                                "video_id": 456,
                                "content": "我也觉得！",
                                "parent_id": 1,
                                "like_count": 2,
                                "created_at": "2024-01-01T12:30:00Z",
                                "updated_at": None,
                                "username": "李四",
                                "avatar": "https://example.com/avatar2.jpg",
                                "replies_count": 0
                            }
                        ]
                    }
                ],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }
