"""
视频响应模型
用于视频相关的响应数据格式
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VideoInfoResponse(BaseModel):
    """
    视频信息响应模型
    """
    id: int = Field(
        ...,
        description="视频ID",
        example=1
    )
    author_id: int = Field(
        ...,
        description="作者ID",
        example=1
    )
    title: str = Field(
        ...,
        description="视频标题",
        example="我的第一个视频"
    )
    description: Optional[str] = Field(
        None,
        description="视频描述",
        example="这是一个很棒的视频"
    )
    play_url: Optional[str] = Field(
        None,
        description="视频播放地址",
        example="https://example.com/video.mp4"
    )
    cover_url: Optional[str] = Field(
        None,
        description="视频封面地址",
        example="https://example.com/cover.jpg"
    )
    duration: int = Field(
        default=0,
        description="视频时长（秒）",
        example=120
    )
    file_size: int = Field(
        default=0,
        description="文件大小（字节）",
        example=10485760
    )
    file_format: Optional[str] = Field(
        None,
        description="文件格式",
        example="mp4"
    )
    width: Optional[int] = Field(
        None,
        description="视频宽度",
        example=1920
    )
    height: Optional[int] = Field(
        None,
        description="视频高度",
        example=1080
    )
    status: str = Field(
        default="pending",
        description="视频状态",
        example="published"
    )
    view_count: int = Field(
        default=0,
        description="播放量",
        example=1000
    )
    favorite_count: int = Field(
        default=0,
        description="点赞数",
        example=50
    )
    comment_count: int = Field(
        default=0,
        description="评论数",
        example=25
    )
    publish_time: Optional[int] = Field(
        None,
        description="发布时间",
        example=1699123200
    )
    created_at: Optional[str] = Field(
        None,
        description="创建时间",
        example="2023-11-05T10:30:00"
    )
    updated_at: Optional[str] = Field(
        None,
        description="更新时间",
        example="2023-11-05T10:30:00"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "author_id": 1,
                "title": "我的第一个视频",
                "description": "这是一个很棒的视频",
                "play_url": "https://example.com/video.mp4",
                "cover_url": "https://example.com/cover.jpg",
                "duration": 120,
                "file_size": 10485760,
                "file_format": "mp4",
                "width": 1920,
                "height": 1080,
                "status": "published",
                "view_count": 1000,
                "favorite_count": 50,
                "comment_count": 25,
                "publish_time": 1699123200,
                "created_at": "2023-11-05T10:30:00",
                "updated_at": "2023-11-05T10:30:00"
            }
        }


class VideoCreateResponse(BaseModel):
    """
    创建视频响应模型
    """
    video_id: int = Field(
        ...,
        description="视频ID",
        example=1
    )
    object_name: str = Field(
        ...,
        description="对象名称",
        example="user_1/video_20231105_103012_abc123.mp4"
    )
    upload_url: str = Field(
        ...,
        description="上传URL",
        example="https://minio.example.com/raw-videos/user_1/video.mp4?presigned"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": 1,
                "object_name": "user_1/video_20231105_103012_abc123.mp4",
                "upload_url": "https://minio.example.com/raw-videos/user_1/video.mp4?presigned"
            }
        }


class VideoUpdateResponse(BaseModel):
    """
    更新视频响应模型
    """
    video_id: int = Field(
        ...,
        description="视频ID",
        example=1
    )
    updated_fields: List[str] = Field(
        ...,
        description="更新的字段",
        example=["title", "description"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": 1,
                "updated_fields": ["title", "description"]
            }
        }


class VideoDeleteResponse(BaseModel):
    """
    删除视频响应模型
    """
    video_id: int = Field(
        ...,
        description="视频ID",
        example=1
    )
    deleted_at: str = Field(
        ...,
        description="删除时间",
        example="2023-11-05T10:30:00"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": 1,
                "deleted_at": "2023-11-05T10:30:00"
            }
        }


class VideoListResponse(BaseModel):
    """
    视频列表响应模型
    """
    videos: List[VideoInfoResponse] = Field(
        ...,
        description="视频列表"
    )
    total: int = Field(
        ...,
        description="总数量",
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
    total_pages: int = Field(
        ...,
        description="总页数",
        example=5
    )

    class Config:
        json_schema_extra = {
            "example": {
                "videos": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }