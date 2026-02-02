"""
评论相关请求模型
"""

from pydantic import BaseModel, Field, validator
from typing import Optional


class CommentCreateRequest(BaseModel):
    """
    创建评论请求模型
    """
    content: str = Field(..., min_length=1, max_length=1000, description="评论内容")
    parent_id: Optional[int] = Field(None, description="父评论ID（用于回复）")
    
    @validator('content')
    def validate_content(cls, v):
        """验证评论内容"""
        if not v or not v.strip():
            raise ValueError('评论内容不能为空')
        # 去除首尾空格
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "这个视频很棒！",
                "parent_id": None
            }
        }


class CommentUpdateRequest(BaseModel):
    """
    更新评论请求模型
    """
    content: str = Field(..., min_length=1, max_length=1000, description="评论内容")
    
    @validator('content')
    def validate_content(cls, v):
        """验证评论内容"""
        if not v or not v.strip():
            raise ValueError('评论内容不能为空')
        # 去除首尾空格
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "更新后的评论内容"
            }
        }
