"""
Agent工厂类 - 创建和管理Agent实例
"""
import logging
from typing import Optional, List, Any
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from app.agent.infra.llm_factory import get_llm

logger = logging.getLogger(__name__)


def create_agent_graph(
    system_prompt: Optional[str] = None,
    tools: Optional[List[BaseTool]] = None
) -> Any:
    """
    创建Agent实例（使用LangGraph）
    
    Args:
        system_prompt: 系统提示词（可选，将通过消息传递）
        tools: 工具列表（可选，如果为None则默认包含搜索工具）
        
    Returns:
        CompiledStateGraph实例（LangGraph Agent）
    """
    # 获取LLM实例
    llm = get_llm()
    
    # 检查LLM是否可用
    if llm is None:
        logger.error("LLM实例不可用，无法创建Agent（请检查DASHSCOPE_API_KEY和LLM_BASE_URL配置）")
        raise ValueError("LLM服务不可用，请检查配置")
    
    # 如果没有提供工具，默认包含搜索工具
    if tools is None:
        from app.agent.tools import create_search_tool
        tools = [create_search_tool()]
    
    try:
        # 使用LangGraph创建Agent（新版本API使用model参数，不支持system_prompt参数）
        # system_prompt 将通过消息列表传递
        agent = create_react_agent(
            model=llm,
            tools=tools
        )
        
        logger.info(f"✓ Agent已创建 - tools: {len(tools)}")
        return agent
    except Exception as e:
        logger.error(f"创建Agent失败: {e}", exc_info=True)
        raise

