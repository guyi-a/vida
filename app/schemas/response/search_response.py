"""
搜索响应模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from app.schemas.response.video_response import VideoInfoResponse


class SearchVideoResponse(BaseModel):
    """
    搜索返回的视频信息（包含高亮）
    """
    id: int = Field(..., description="视频ID")
    author_id: int = Field(..., description="作者ID")
    author_name: Optional[str] = Field(None, description="作者名称")
    title: str = Field(..., description="视频标题")
    description: Optional[str] = Field(None, description="视频描述")
    cover_url: Optional[str] = Field(None, description="封面URL")
    play_url: Optional[str] = Field(None, description="播放URL")
    view_count: int = Field(default=0, description="播放量")
    favorite_count: int = Field(default=0, description="点赞数")
    comment_count: int = Field(default=0, description="评论数")
    publish_time: Optional[int] = Field(None, description="发布时间")
    highlight: Optional[Dict[str, List[str]]] = Field(
        None,
        description="搜索高亮结果",
        example={
            "title": ["<em>Python</em>教程"],
            "description": ["这是一个<em>Python</em>学习视频"]
        }
    )


class SearchResponse(BaseModel):
    """
    搜索响应模型
    """
    videos: List[SearchVideoResponse] = Field(
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

