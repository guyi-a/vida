"""
对话响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional


class ChatResponse(BaseModel):
    """
    对话响应模型
    """
    code: int = Field(
        default=200,
        description="响应状态码",
        example=200
    )
    message: str = Field(
        default="success",
        description="响应消息",
        example="success"
    )
    data: Optional[dict] = Field(
        None,
        description="响应数据"
    )
    ai_reply: Optional[str] = Field(
        None,
        description="AI回复内容"
    )
    chat_id: Optional[str] = Field(
        None,
        description="对话ID"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "data": None,
                "ai_reply": "为你找到超贴合的视频！👇\n\n1. 【猫咪沉浸式拆家名场面】#萌宠 #搞笑 → 全程高能...",
                "chat_id": "chat_1234567890"
            }
        }

