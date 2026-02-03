"""
LLM服务 - 使用LangChain封装大模型调用
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional, AsyncIterator
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage

logger = logging.getLogger(__name__)


class LLMService:
    """LLM服务类 - 封装LangChain大模型调用"""
    
    def __init__(self, prompt_file: Optional[str] = None):
        """
        初始化LLM服务
        
        Args:
            prompt_file: 提示词文件路径（相对于项目根目录），默认为 search_agent_prompt.md
        """
        from app.agent.infra.llm_factory import get_llm
        self.llm = get_llm()
        
        # 加载系统提示词
        self.system_prompt = self._load_prompt(prompt_file)
        
        logger.info("✓ LLM服务已初始化")
    
    def _load_prompt(self, prompt_file: Optional[str] = None) -> str:
        """
        加载提示词文件
        
        Args:
            prompt_file: 提示词文件路径，默认为 app/agent/prompts/search_agent_prompt.md
            
        Returns:
            提示词内容字符串
        """
        if prompt_file is None:
            # 默认使用搜索智能体提示词
            prompt_file = "app/agent/prompts/search_agent_prompt.md"
        
        try:
            # 获取项目根目录
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            prompt_path = project_root / prompt_file
            
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f"✓ 已加载提示词文件: {prompt_file}")
                return content
            else:
                logger.warning(f"提示词文件不存在: {prompt_path}，将使用空提示词")
                return ""
        except Exception as e:
            logger.error(f"加载提示词文件失败: {e}", exc_info=True)
            return ""
    
    def _convert_messages(self, messages: List[Dict], add_system_prompt: bool = True) -> List[BaseMessage]:
        """
        将消息字典列表转换为LangChain Message对象
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            add_system_prompt: 是否自动添加系统提示词（如果消息中没有system消息）
            
        Returns:
            LangChain Message对象列表
        """
        langchain_messages = []
        
        # 检查是否已有system消息
        has_system = any(msg.get("role") == "system" for msg in messages)
        
        # 如果没有system消息且需要添加系统提示词，则添加
        if add_system_prompt and not has_system and self.system_prompt:
            langchain_messages.append(SystemMessage(content=self.system_prompt))
        
        # 转换消息
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
        
        return langchain_messages
    
    async def ainvoke(self, messages: List[Dict]) -> str:
        """
        异步非流式调用LLM
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            
        Returns:
            AI回复文本
        """
        if not self.llm:
            return "抱歉，AI服务暂不可用，请检查配置。"
        
        try:
            # 转换消息格式
            langchain_messages = self._convert_messages(messages)
            
            # 异步调用大模型
            response = await self.llm.ainvoke(langchain_messages)
            
            # 提取回复内容
            if hasattr(response, 'content'):
                return response.content.strip()
            elif isinstance(response, str):
                return response.strip()
            else:
                return str(response).strip()
        except Exception as e:
            logger.error(f"LLM调用失败: {e}", exc_info=True)
            return f"抱歉，对话过程中出现错误：{str(e)}"
    
    async def stream(self, messages: List[Dict]) -> AsyncIterator[str]:
        """
        流式调用LLM
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            
        Yields:
            AI回复的文本片段（逐字或逐词）
        """
        if not self.llm:
            yield "抱歉，AI服务暂不可用，请检查配置。"
            return
        
        try:
            # 转换消息格式
            langchain_messages = self._convert_messages(messages)
            
            # 流式调用大模型（使用astream进行异步流式调用）
            async for chunk in self.llm.astream(langchain_messages):
                if hasattr(chunk, 'content'):
                    yield chunk.content
                elif isinstance(chunk, str):
                    yield chunk
                else:
                    # 如果chunk是AIMessage对象，提取content
                    if hasattr(chunk, 'content'):
                        yield chunk.content
        except Exception as e:
            logger.error(f"LLM流式调用失败: {e}", exc_info=True)
            yield f"抱歉，对话过程中出现错误：{str(e)}"
    
    def is_available(self) -> bool:
        """检查LLM服务是否可用"""
        return self.llm is not None


# 全局单例
_llm_service_instance: Optional[LLMService] = None


def get_llm_service(prompt_file: Optional[str] = None) -> LLMService:
    """
    获取LLM服务单例
    
    Args:
        prompt_file: 提示词文件路径（可选），仅在首次创建时生效
    
    Returns:
        LLMService实例
    """
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService(prompt_file=prompt_file)
    return _llm_service_instance

