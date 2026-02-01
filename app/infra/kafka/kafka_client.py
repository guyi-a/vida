"""
Kafka客户端工具类
提供Kafka消息队列的生产者和消费者封装
"""

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import json
import logging
from typing import Optional, Dict, Any, Callable

from app.core.config import settings


class KafkaClient:
    """
    Kafka客户端封装类
    提供生产者和消费者的简化接口
    """
    
    def __init__(self):
        """初始化Kafka客户端"""
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.transcode_topic = settings.KAFKA_TRANSCODE_TOPIC
        self.group_id = settings.KAFKA_GROUP_ID
        
        # 生产者实例
        self._producer: Optional[KafkaProducer] = None
        # 消费者实例
        self._consumer: Optional[KafkaConsumer] = None
        
        self.logger = logging.getLogger(__name__)
    
    @property
    def producer(self) -> KafkaProducer:
        """获取Kafka生产者实例（懒加载）"""
        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                # 连接参数
                api_version_auto_timeout_ms=10000,
                # 重试配置
                retries=3,
                retry_backoff_ms=1000,
                # 批量配置
                batch_size=16384,
                linger_ms=100,
                # 缓冲区配置
                buffer_memory=33554432,
            )
        return self._producer
    
    @property
    def consumer(self) -> KafkaConsumer:
        """获取Kafka消费者实例（懒加载）"""
        if self._consumer is None:
            self._consumer = KafkaConsumer(
                self.transcode_topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                key_deserializer=lambda x: x.decode('utf-8') if x else None,
                # 消费者配置
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=5000,
                # 超时配置
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                max_poll_interval_ms=300000,
                # 批量获取配置
                max_poll_records=500,
                fetch_max_wait_ms=500,
                fetch_min_bytes=1,
            )
        return self._consumer
    
    def send_message(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        发送消息到指定主题
        
        Args:
            topic: 主题名称
            value: 消息内容（字典格式）
            key: 消息键（可选）
            headers: 消息头（可选）
            
        Returns:
            发送是否成功
        """
        try:
            # 转换headers格式
            kafka_headers = None
            if headers:
                kafka_headers = [(k, v.encode('utf-8')) for k, v in headers.items()]
            
            # 发送消息
            future = self.producer.send(
                topic=topic,
                value=value,
                key=key,
                headers=kafka_headers
            )
            
            # 等待发送完成
            record_metadata = future.get(timeout=10)
            
            self.logger.info(
                f"消息发送成功 - Topic: {record_metadata.topic}, "
                f"Partition: {record_metadata.partition}, "
                f"Offset: {record_metadata.offset}"
            )
            
            return True
            
        except KafkaError as e:
            self.logger.error(f"发送Kafka消息失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"发送消息时发生未知错误: {e}")
            return False
    
    def send_transcode_task(
        self,
        task_data: Dict[str, Any]
    ) -> bool:
        """
        发送视频转码任务消息
        
        Args:
            task_data: 转码任务数据
            
        Returns:
            发送是否成功
        """
        required_fields = ['video_id', 'raw_file_path', 'user_id']
        
        # 验证必需字段
        for field in required_fields:
            if field not in task_data:
                raise ValueError(f"转码任务缺少必需字段: {field}")
        
        # 添加任务元数据
        task_message = {
            **task_data,
            'task_type': 'video_transcode',
            'timestamp': __import__('time').time(),
            'status': 'pending'
        }
        
        return self.send_message(
            topic=self.transcode_topic,
            value=task_message,
            key=str(task_data['video_id']),  # 使用video_id作为消息键
            headers={'task_type': 'video_transcode'}
        )
    
    def consume_messages(self, message_handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        消费消息并处理
        
        Args:
            message_handler: 消息处理函数
        """
        try:
            self.logger.info(f"开始消费主题: {self.transcode_topic}")
            
            for message in self.consumer:
                try:
                    # 调用消息处理器
                    message_handler(message.value)
                    
                    self.logger.info(
                        f"消息处理完成 - Offset: {message.offset}, "
                        f"Key: {message.key}"
                    )
                    
                except Exception as e:
                    self.logger.error(
                        f"处理消息失败 - Offset: {message.offset}, "
                        f"Error: {e}"
                    )
                    # 记录失败消息以便后续处理
                    self._handle_failed_message(message.value, e)
                    
        except KafkaError as e:
            self.logger.error(f"Kafka消费者错误: {e}")
            raise
        except KeyboardInterrupt:
            self.logger.info("消费者被用户中断")
        finally:
            self.close_consumer()
    
    def _handle_failed_message(self, message_value: Dict[str, Any], error: Exception) -> None:
        """
        处理失败的消息
        
        Args:
            message_value: 消息内容
            error: 错误信息
        """
        # TODO: 可以实现重试逻辑或死信队列
        error_info = {
            'failed_message': message_value,
            'error': str(error),
            'retry_count': 0,
            'timestamp': __import__('time').time()
        }
        
        self.logger.error(f"消息处理失败: {error_info}")
    
    def close_producer(self) -> None:
        """关闭生产者"""
        if self._producer is not None:
            self._producer.flush()
            self._producer.close()
            self._producer = None
    
    def close_consumer(self) -> None:
        """关闭消费者"""
        if self._consumer is not None:
            self._consumer.close()
            self._consumer = None
    
    def close(self) -> None:
        """关闭所有连接"""
        self.close_producer()
        self.close_consumer()
    
    def __enter__(self):
        """上下文管理器进入"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()


# 创建全局Kafka客户端实例
kafka_client = KafkaClient()