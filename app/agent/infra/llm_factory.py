"""
LLM工厂类 - 统一创建和管理LLM实例
"""
from langchain_openai import ChatOpenAI
from app.core.config import settings


def get_llm() -> ChatOpenAI:
    """
    获取LLM实例（使用固定模型名称）
    
    Returns:
        LLM实例
    """
    return ChatOpenAI(
        temperature=0.3,
        max_tokens=50000,
        timeout=None,
        max_retries=2,
        base_url=settings.LLM_BASE_URL,
        api_key=settings.DASHSCOPE_API_KEY,
        model=settings.LLM_MODEL
    )

