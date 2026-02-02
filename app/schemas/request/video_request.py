"""
视频请求模型
用于视频相关的请求数据验证
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VideoCreateRequest(BaseModel):
    """
    创建视频请求模型
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="视频标题",
        example="我的第一个视频"
    )
    description: Optional[str] = Field(
        None,
        description="视频描述",
        example="这是一个很棒的视频"
    )
    file_format: Optional[str] = Field(
        None,
        description="文件格式",
        example="mp4"
    )
    width: Optional[int] = Field(
        None,
        gt=0,
        description="视频宽度",
        example=1920
    )
    height: Optional[int] = Field(
        None,
        gt=0,
        description="视频高度",
        example=1080
    )
    duration: Optional[int] = Field(
        None,
        ge=0,
        description="视频时长（秒）",
        example=120
    )
    file_size: Optional[int] = Field(
        None,
        ge=0,
        description="文件大小（字节）",
        example=10485760
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "我的第一个视频",
                "description": "这是一个很棒的视频",
                "file_format": "mp4",
                "width": 1920,
                "height": 1080,
                "duration": 120,
                "file_size": 10485760
            }
        }


class VideoUpdateRequest(BaseModel):
    """
    更新视频请求模型
    """
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="视频标题",
        example="更新后的视频标题"
    )
    description: Optional[str] = Field(
        None,
        description="视频描述",
        example="更新后的视频描述"
    )
    status: Optional[str] = Field(
        None,
        description="视频状态（pending/processing/published/failed/deleted）",
        example="published"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "更新后的视频标题",
                "description": "更新后的视频描述",
                "status": "published"
            }
        }


class VideoPublishRequest(BaseModel):
    """
    视频发布请求模型
    """
    publish_now: bool = Field(
        default=True,
        description="是否立即发布",
        example=True
    )
    publish_time: Optional[int] = Field(
        None,
        description="发布时间（Unix时间戳）",
        example=1699123200
    )

    class Config:
        json_schema_extra = {
            "example": {
                "publish_now": True,
                "publish_time": None
            }
        }


class VideoListRequest(BaseModel):
    """
    视频列表请求模型
    """
    page: int = Field(
        default=1,
        ge=1,
        description="页码",
        example=1
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="每页数量",
        example=20
    )
    status: Optional[str] = Field(
        None,
        description="状态筛选",
        example="published"
    )
    author_id: Optional[int] = Field(
        None,
        description="作者ID筛选",
        example=1
    )
    search: Optional[str] = Field(
        None,
        description="搜索关键词（标题或描述）",
        example="教程"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20,
                "status": "published",
                "author_id": 1,
                "search": "教程"
            }
        }