from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """
    基础响应模型
    提供统一的响应结构
    """
    success: bool = Field(
        default=True,
        description="请求是否成功",
        example=True
    )
    message: str = Field(
        default="操作成功",
        description="响应消息",
        example="操作成功"
    )
    data: Optional[T] = Field(
        None,
        description="响应数据"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": None
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应模型
    """
    success: bool = Field(
        default=True,
        description="请求是否成功",
        example=True
    )
    message: str = Field(
        default="操作成功",
        description="响应消息",
        example="操作成功"
    )
    data: Optional[T] = Field(
        None,
        description="响应数据"
    )
    meta: dict = Field(
        default_factory=dict,
        description="分页元数据"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": None,
                "meta": {
                    "page": 1,
                    "page_size": 20,
                    "total": 100,
                    "total_pages": 5
                }
            }
        }