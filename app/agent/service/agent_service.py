"""
Agent服务 - 使用LangGraph封装Agent调用
支持异步和流式调用
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional, AsyncIterator, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from app.agent.infra.agent_factory import create_agent_graph

logger = logging.getLogger(__name__)


class AgentService:
    """Agent服务类 - 封装LangGraph Agent调用"""
    
    def __init__(self, tools: Optional[List] = None, prompt_file: Optional[str] = None):
        """
        初始化Agent服务
        
        Args:
            tools: 工具列表（可选，默认为空列表，后续添加搜索工具时传入）
            prompt_file: 提示词文件路径（可选，默认为 search_agent_prompt.md）
        """
        # 加载系统提示词（保存为实例变量，后续通过消息传递）
        self.system_prompt = self._load_prompt(prompt_file)
        
        # 使用agent_factory创建Agent（不再传递system_prompt参数）
        # 注意：如果 tools 为 None，传递 None 而不是 []，这样 agent_factory 会自动加载搜索工具
        self.agent = create_agent_graph(
            system_prompt=None,  # 不再作为参数传递
            tools=tools  # 传递 None 时会自动加载搜索工具
        )
        
        logger.info(f"✓ Agent服务已初始化 - tools: {len(tools) if tools else 0}")
    
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
    
    def _convert_messages(self, messages: List[Dict]) -> List[BaseMessage]:
        """
        将消息字典列表转换为LangChain Message对象
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            
        Returns:
            LangChain Message对象列表
        """
        langchain_messages = []
        
        # 检查是否已有系统消息
        has_system_message = any(msg.get("role") == "system" for msg in messages)
        
        # 如果没有系统消息且有系统提示词，则添加系统提示词
        if not has_system_message and self.system_prompt:
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
    
    async def ainvoke(self, messages: List[Dict], **kwargs: Any) -> str:
        """
        异步非流式调用Agent
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            **kwargs: 其他参数，会传递给Agent
            
        Returns:
            Agent回复文本
        """
        if not self.agent:
            return "抱歉，Agent服务暂不可用，请检查配置。"
        
        try:
            # 转换消息格式为 LangChain 格式
            langchain_messages = self._convert_messages(messages)
            
            if not langchain_messages:
                return "请输入您的问题。"
            
            # 准备输入 - LangGraph 使用 messages 作为输入
            agent_input = {"messages": langchain_messages}
            agent_input.update(kwargs)
            
            # 异步调用Agent
            result = await self.agent.ainvoke(agent_input)
            
            # 提取回复内容
            if isinstance(result, dict):
                # LangGraph 返回 messages 列表
                if "messages" in result:
                    messages_list = result["messages"]
                    # 获取最后一条 AI 消息
                    for msg in reversed(messages_list):
                        if isinstance(msg, AIMessage):
                            return msg.content.strip() if msg.content else ""
                # 兼容其他格式
                output = result.get("output", "")
                if output:
                    return output.strip()
                return str(result).strip()
            elif isinstance(result, str):
                return result.strip()
            else:
                return str(result).strip()
                
        except Exception as e:
            logger.error(f"Agent调用失败: {e}", exc_info=True)
            return f"抱歉，对话过程中出现错误：{str(e)}"
    
    async def stream(self, messages: List[Dict], **kwargs: Any) -> AsyncIterator[str]:
        """
        流式调用Agent
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            **kwargs: 其他参数，会传递给Agent
            
        Yields:
            Agent回复的文本片段（逐字或逐词）
        """
        if not self.agent:
            yield "抱歉，Agent服务暂不可用，请检查配置。"
            return
        
        try:
            # 转换消息格式为 LangChain 格式
            langchain_messages = self._convert_messages(messages)
            
            if not langchain_messages:
                yield "请输入您的问题。"
                return
            
            # 准备输入 - LangGraph 使用 messages 作为输入
            agent_input = {"messages": langchain_messages}
            agent_input.update(kwargs)
            
            # 流式调用Agent
            # LangGraph 的流式返回格式：使用 stream_mode="values" 获取完整状态
            # 每次迭代返回当前的完整消息列表，从中提取最新的AI回复
            full_output = ""
            # 记录输入消息的数量，用于区分新增的AI消息
            input_message_count = len(langchain_messages)
            
            async for state in self.agent.astream(agent_input, stream_mode="values"):
                try:
                    # state 是一个字典，包含 "messages" 键
                    if isinstance(state, dict) and "messages" in state:
                        messages = state["messages"]
                        # 只处理新增的消息（索引 >= input_message_count 的消息）
                        new_messages = messages[input_message_count:]
                        
                        # 找到最后一条 AIMessage（从新消息中）
                        for msg in reversed(new_messages):
                            if isinstance(msg, AIMessage) and msg.content:
                                current_content = str(msg.content)
                                # 提取增量内容
                                if len(current_content) > len(full_output):
                                    new_content = current_content[len(full_output):]
                                    full_output = current_content
                                    if new_content:
                                        yield new_content
                                break  # 只处理最后一条新增的 AIMessage
                            
                except Exception as e:
                    logger.warning(f"处理流式chunk时出错: {e}, state类型: {type(state)}")
                    continue
                        
        except Exception as e:
            logger.error(f"Agent流式调用失败: {e}", exc_info=True)
            yield f"抱歉，对话过程中出现错误：{str(e)}"
    
    def is_available(self) -> bool:
        """检查Agent服务是否可用"""
        return self.agent is not None


# 全局单例
_agent_service_instance: Optional[AgentService] = None


def get_agent_service(tools: Optional[List] = None) -> AgentService:
    """
    获取Agent服务单例
    
    Args:
        tools: 工具列表（可选），仅在首次创建时生效
    
    Returns:
        AgentService实例
    """
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AgentService(tools=tools)
    return _agent_service_instance

