"""
对话记忆存储服务 - 使用Redis统一管理对话历史
"""
import json
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse

try:
    import redis
except ImportError:
    redis = None

try:
    import tiktoken
except ImportError:
    tiktoken = None

logger = logging.getLogger(__name__)


class MemoryStore:
    """对话记忆存储服务"""
    
    def __init__(
        self,
        redis_url: str = None,
        max_tokens: int = 2000,  # 默认最大token数
        encoding_name: str = "cl100k_base"  # tiktoken编码名称
    ):
        """
        初始化MemoryStore
        
        Args:
            redis_url: Redis连接URL，格式: redis://localhost:6379/0
            max_tokens: 最大token数，超过后会自动删除最旧的消息
            encoding_name: tiktoken编码名称，默认使用cl100k_base（GPT-4等模型使用）
        """
        self.redis_client = None
        
        # 解析Redis URL
        if redis_url:
            parsed = urlparse(redis_url)
            redis_host = parsed.hostname or "localhost"
            redis_port = parsed.port or 6379
            redis_db = int(parsed.path.lstrip('/')) if parsed.path else 0
        else:
            # 从环境变量或配置读取
            from app.core.config import settings
            parsed = urlparse(settings.REDIS_URL)
            redis_host = parsed.hostname or "localhost"
            redis_port = parsed.port or 6379
            redis_db = int(parsed.path.lstrip('/')) if parsed.path else 0
        
        if redis:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                # 测试连接
                self.redis_client.ping()
                logger.info("✓ Redis连接成功")
            except Exception as e:
                logger.warning(f"Redis连接失败，对话记忆将不会持久化: {e}")
                self.redis_client = None
        else:
            logger.warning("Redis未安装，对话记忆将不会持久化")
        
        # 初始化tiktoken编码器
        if tiktoken:
            try:
                self.encoding = tiktoken.get_encoding(encoding_name)
                logger.info(f"✓ tiktoken编码器已初始化: {encoding_name}")
            except Exception as e:
                logger.error(f"tiktoken初始化失败: {e}")
                self.encoding = None
        else:
            logger.warning("tiktoken未安装，将使用字符数估算token")
            self.encoding = None
        
        self.max_tokens = max_tokens
    
    def _get_key(self, user_id: str, chat_id: str) -> str:
        """生成Redis键"""
        return f"messages:{user_id}:{chat_id}"
    
    def _count_tokens(self, text: str) -> int:
        """
        计算文本的token数量
        
        Args:
            text: 文本内容
            
        Returns:
            token数量
        """
        if not self.encoding:
            # 如果tiktoken不可用，使用简单的字符数估算（1 token ≈ 4字符）
            return len(text) // 4
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.warning(f"token计算失败: {e}，使用字符数估算")
            return len(text) // 4
    
    def _count_messages_tokens(self, messages: List[Dict]) -> int:
        """
        计算消息列表的总token数
        
        Args:
            messages: 消息列表
            
        Returns:
            总token数
        """
        total = 0
        for msg in messages:
            # 计算role和content的token数
            role_tokens = self._count_tokens(msg.get("role", ""))
            content_tokens = self._count_tokens(msg.get("content", ""))
            # 加上一些格式开销（估算）
            total += role_tokens + content_tokens + 5  # 5个token用于格式开销
        return total
    
    def _truncate_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        截断消息列表，删除最旧的消息直到token数在限制内
        
        Args:
            messages: 消息列表
            
        Returns:
            截断后的消息列表
        """
        if not messages:
            return messages
        
        total_tokens = self._count_messages_tokens(messages)
        
        # 如果token数在限制内，直接返回
        if total_tokens <= self.max_tokens:
            return messages
        
        # 从最旧的消息开始删除
        truncated = messages.copy()
        while truncated and self._count_messages_tokens(truncated) > self.max_tokens:
            truncated.pop(0)  # 删除最旧的消息
        
        logger.info(f"消息已截断: {len(messages)} -> {len(truncated)} 条消息")
        return truncated
    
    async def get_records(self, user_id: str, chat_id: str) -> List[Dict]:
        """
        获取对话记录
        
        Args:
            user_id: 用户ID
            chat_id: 对话ID
            
        Returns:
            消息列表，格式: [{"role": "user", "content": "..."}, ...]
        """
        if not self.redis_client:
            logger.warning("Redis未连接，返回空记录")
            return []
        
        try:
            key = self._get_key(user_id, chat_id)
            value = self.redis_client.get(key)
            
            if not value:
                return []
            
            # 反序列化JSON字符串
            messages = json.loads(value)
            
            # 确保是列表格式
            if not isinstance(messages, list):
                logger.warning(f"对话记录格式错误: {user_id}:{chat_id}")
                return []
            
            return messages
        except json.JSONDecodeError as e:
            logger.error(f"反序列化对话记录失败: {user_id}:{chat_id}, {e}")
            return []
        except Exception as e:
            logger.error(f"获取对话记录失败: {user_id}:{chat_id}, {e}")
            return []
    
    async def save_records(self, user_id: str, chat_id: str, messages: List[Dict]):
        """
        保存对话记录
        
        Args:
            user_id: 用户ID
            chat_id: 对话ID
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
        """
        if not self.redis_client:
            logger.warning("Redis未连接，无法保存记录")
            return
        
        try:
            # 截断消息（如果超过token限制）
            truncated_messages = self._truncate_messages(messages)
            
            # 序列化为JSON字符串
            value = json.dumps(truncated_messages, ensure_ascii=False)
            
            # 保存到Redis
            key = self._get_key(user_id, chat_id)
            self.redis_client.set(key, value)
            
            logger.debug(f"对话记录已保存: {user_id}:{chat_id}, {len(truncated_messages)} 条消息")
        except Exception as e:
            logger.error(f"保存对话记录失败: {user_id}:{chat_id}, {e}")
    
    async def append_message(self, user_id: str, chat_id: str, role: str, content: str):
        """
        追加一条消息到对话记录
        
        Args:
            user_id: 用户ID
            chat_id: 对话ID
            role: 角色 ("user" 或 "assistant")
            content: 消息内容
        """
        # 获取现有记录
        messages = await self.get_records(user_id, chat_id)
        
        # 追加新消息
        messages.append({
            "role": role,
            "content": content
        })
        
        # 保存记录
        await self.save_records(user_id, chat_id, messages)
    
    async def delete_records(self, user_id: str, chat_id: str):
        """
        删除对话记录
        
        Args:
            user_id: 用户ID
            chat_id: 对话ID
        """
        if not self.redis_client:
            return
        
        try:
            key = self._get_key(user_id, chat_id)
            self.redis_client.delete(key)
            logger.info(f"对话记录已删除: {user_id}:{chat_id}")
        except Exception as e:
            logger.error(f"删除对话记录失败: {user_id}:{chat_id}, {e}")
    
    def _get_chat_list_key(self, user_id: str) -> str:
        """生成chat_id列表的Redis键"""
        return f"chat_list:{user_id}"
    
    async def add_chat_id(self, user_id: str, chat_id: str):
        """
        添加chat_id到列表
        
        Args:
            user_id: 用户ID
            chat_id: 对话ID
        """
        if not self.redis_client:
            return
        
        try:
            key = self._get_chat_list_key(user_id)
            # 使用Redis Set存储chat_id列表
            self.redis_client.sadd(key, chat_id)
            logger.debug(f"chat_id已添加到列表: {user_id}:{chat_id}")
        except Exception as e:
            logger.error(f"添加chat_id到列表失败: {user_id}:{chat_id}, {e}")
    
    async def get_chat_list(self, user_id: str) -> List[str]:
        """
        获取指定用户的所有chat_id列表
        
        Args:
            user_id: 用户ID
        
        Returns:
            chat_id列表
        """
        if not self.redis_client:
            return []
        
        try:
            key = self._get_chat_list_key(user_id)
            # 获取Set中的所有成员
            chat_ids = list(self.redis_client.smembers(key))
            # 按创建时间倒序排列（chat_id包含时间戳，可以简单排序）
            chat_ids.sort(reverse=True)
            return chat_ids
        except Exception as e:
            logger.error(f"获取chat_id列表失败: {user_id}, {e}")
            return []
    
    async def delete_chat_id(self, user_id: str, chat_id: str):
        """
        从列表中删除chat_id（同时删除对应的对话记录）
        
        Args:
            user_id: 用户ID
            chat_id: 对话ID
        """
        if not self.redis_client:
            return
        
        try:
            # 从列表中删除
            key = self._get_chat_list_key(user_id)
            self.redis_client.srem(key, chat_id)
            
            # 同时删除对话记录
            await self.delete_records(user_id, chat_id)
            
            logger.info(f"chat_id已从列表删除: {user_id}:{chat_id}")
        except Exception as e:
            logger.error(f"从列表删除chat_id失败: {user_id}:{chat_id}, {e}")
    
    async def get_chat_preview(self, user_id: str, chat_id: str) -> Optional[Dict]:
        """
        获取对话预览信息（第一条消息）
        
        Args:
            user_id: 用户ID
            chat_id: 对话ID
            
        Returns:
            预览信息: {"chat_id": str, "preview": str, "message_count": int}
        """
        messages = await self.get_records(user_id, chat_id)
        if not messages:
            return None
        
        # 获取第一条用户消息作为预览
        preview = ""
        for msg in messages:
            if msg.get("role") == "user":
                preview = msg.get("content", "")[:50]  # 最多50字符
                break
        
        return {
            "chat_id": chat_id,
            "preview": preview or "新对话",
            "message_count": len(messages)
        }
    
    def is_available(self) -> bool:
        """检查Redis是否可用"""
        return self.redis_client is not None


# 全局单例
_memory_store_instance: Optional[MemoryStore] = None


def get_memory_store(
    redis_url: str = None,
    max_tokens: int = 2000
) -> MemoryStore:
    """
    获取MemoryStore单例
    
    Args:
        redis_url: Redis连接URL，如果为None则从配置读取
        max_tokens: 最大token数
        
    Returns:
        MemoryStore实例
    """
    global _memory_store_instance
    if _memory_store_instance is None:
        _memory_store_instance = MemoryStore(
            redis_url=redis_url,
            max_tokens=max_tokens
        )
    return _memory_store_instance

