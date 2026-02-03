"""
Agent对话API
使用Agent模式调用
"""
import logging
import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from app.agent.service.agent_service import get_agent_service
from app.agent.context.memory_store import get_memory_store
from app.schemas.request.chat_request import ChatRequest
from app.schemas.response.chat_response import ChatResponse
from app.core.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent", tags=["Agent对话"])


@router.post("/invoke", response_model=ChatResponse)
async def invoke_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    同步调用Agent对话接口
    接收用户消息，返回完整AI回复
    
    需要传入参数：
    - message: 用户消息
    - chat_id: 对话ID
    """
    try:
        message = request.message.strip()
        if not message:
            return ChatResponse(
                code=400,
                message="消息不能为空",
                data=None,
                ai_reply=None,
                chat_id=None
            )
        
        # 验证必需参数
        if not request.chat_id:
            return ChatResponse(
                code=400,
                message="chat_id不能为空，请先创建会话",
                data=None,
                ai_reply=None,
                chat_id=None
            )
        
        # 获取用户ID（从current_user获取）
        user_id = str(current_user.id)
        chat_id = request.chat_id
        
        # 获取服务实例
        memory_store = get_memory_store()
        agent_service = get_agent_service()
        
        if not agent_service.is_available():
            return ChatResponse(
                code=503,
                message="Agent服务暂不可用，请检查配置",
                data=None,
                ai_reply=None,
                chat_id=None
            )
        
        # 获取对话历史
        memory_messages = await memory_store.get_records(user_id, chat_id)
        
        # 添加用户消息
        memory_messages.append({
            "role": "user",
            "content": message
        })
        
        # 调用Agent（异步非流式）
        ai_reply = await agent_service.ainvoke(memory_messages)
        
        # 添加AI回复
        memory_messages.append({
            "role": "assistant",
            "content": ai_reply
        })
        
        # 保存更新后的消息
        await memory_store.save_records(user_id, chat_id, memory_messages)
        
        # 确保chat_id在列表中
        await memory_store.add_chat_id(user_id, chat_id)
        
        return ChatResponse(
            code=200,
            message="success",
            data=None,
            ai_reply=ai_reply,
            chat_id=chat_id
        )
    except Exception as e:
        logger.error(f"Agent对话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent对话失败: {str(e)}")


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    流式返回Agent对话接口
    接收用户消息，流式返回AI回复
    
    需要传入参数：
    - message: 用户消息
    - chat_id: 对话ID
    """
    try:
        message = request.message.strip()
        if not message:
            async def error_response():
                chunk = {
                    "code": 400,
                    "message": "消息不能为空",
                    "data": None
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            
            return StreamingResponse(
                error_response(),
                media_type="text/event-stream"
            )
        
        # 验证必需参数
        if not request.chat_id:
            async def error_response():
                chunk = {
                    "code": 400,
                    "message": "chat_id不能为空，请先创建会话",
                    "data": None
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            
            return StreamingResponse(
                error_response(),
                media_type="text/event-stream"
            )
        
        # 获取用户ID（从current_user获取）
        user_id = str(current_user.id)
        chat_id = request.chat_id
        
        # 获取服务实例
        memory_store = get_memory_store()
        agent_service = get_agent_service()
        
        if not agent_service.is_available():
            async def error_response():
                chunk = {
                    "code": 503,
                    "message": "Agent服务暂不可用，请检查配置",
                    "data": None
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            
            return StreamingResponse(
                error_response(),
                media_type="text/event-stream"
            )
        
        # 获取对话历史
        memory_messages = await memory_store.get_records(user_id, chat_id)
        
        # 添加用户消息
        memory_messages.append({
            "role": "user",
            "content": message
        })
        
        async def generate_response():
            """生成流式响应"""
            full_reply = ""
            
            try:
                # 流式调用Agent
                async for chunk in agent_service.stream(memory_messages):
                    full_reply += chunk
                    
                    # 发送流式数据块
                    data_chunk = {
                        "code": 200,
                        "message": "streaming",
                        "data": {
                            "content": chunk
                        }
                    }
                    yield f"data: {json.dumps(data_chunk, ensure_ascii=False)}\n\n"
                
                # 添加AI回复到历史
                memory_messages.append({
                    "role": "assistant",
                    "content": full_reply
                })
                
                # 保存更新后的消息（用户消息 + AI回复一起保存）
                await memory_store.save_records(user_id, chat_id, memory_messages)
                
                # 确保chat_id在列表中
                await memory_store.add_chat_id(user_id, chat_id)
                
                # 发送结束标记（包含chat_id）
                end_chunk = {
                    "code": 200,
                    "message": "done",
                    "data": {
                        "chat_id": chat_id
                    }
                }
                yield f"data: {json.dumps(end_chunk, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error(f"流式Agent对话失败: {e}", exc_info=True)
                error_chunk = {
                    "code": 500,
                    "message": f"对话过程中出现错误：{str(e)}",
                    "data": None
                }
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"流式Agent对话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"流式Agent对话失败: {str(e)}")

