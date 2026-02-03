"""
搜索请求模型
"""

from pydantic import BaseModel, Field
from typing import Optional


class SearchRequest(BaseModel):
    """
    视频搜索请求模型
    """
    q: Optional[str] = Field(
        None,
        description="搜索关键词（标题/描述）",
        example="Python教程"
    )
    author_id: Optional[int] = Field(
        None,
        description="作者ID",
        example=123
    )
    video_id: Optional[int] = Field(
        None,
        description="视频ID（精确匹配）",
        example=456
    )
    sort: Optional[str] = Field(
        "relevance",
        description="排序方式：relevance(相关性)/time(时间)/hot(热度)",
        example="hot"
    )
    start_time: Optional[int] = Field(
        None,
        description="开始时间（Unix时间戳）",
        example=1699123200
    )
    end_time: Optional[int] = Field(
        None,
        description="结束时间（Unix时间戳）",
        example=1701715200
    )
    page: int = Field(
        1,
        ge=1,
        description="页码",
        example=1
    )
    page_size: int = Field(
        20,
        ge=1,
        le=100,
        description="每页数量",
        example=20
    )

    class Config:
        json_schema_extra = {
            "example": {
                "q": "Python教程",
                "sort": "hot",
                "page": 1,
                "page_size": 20
            }
        }

