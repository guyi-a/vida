"""
对话请求模型
"""
from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """
    对话请求模型
    """
    message: str = Field(
        ...,
        description="用户消息",
        example="帮我找一些搞笑的猫咪视频"
    )
    chat_id: str = Field(
        ...,
        description="对话ID",
        example="chat_1234567890"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "帮我找一些搞笑的猫咪视频",
                "chat_id": "chat_1234567890"
            }
        }

