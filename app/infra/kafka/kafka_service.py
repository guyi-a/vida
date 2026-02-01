"""
Kafka业务服务层
封装转码任务相关的消息生产和消费
"""

from typing import Dict, Any, Callable
from datetime import datetime
import uuid

from app.core.config import settings
from .kafka_client import kafka_client


class TranscodeTaskMessage:
    """
    转码任务消息格式定义
    """
    
    def __init__(
        self,
        video_id: int,
        raw_file_path: str,
        user_id: int,
        **kwargs
    ):
        self.video_id = video_id
        self.raw_file_path = raw_file_path
        self.user_id = user_id
        
        # 可选参数
        self.title: str = kwargs.get('title', '')
        self.description: str = kwargs.get('description', '')
        self.quality: str = kwargs.get('quality', '720p')  # 转码质量：480p, 720p, 1080p
        self.format: str = kwargs.get('format', 'mp4')     # 输出格式
        self.generate_cover: bool = kwargs.get('generate_cover', True)  # 是否生成封面
        
        # 任务元数据
        self.task_id: str = str(uuid.uuid4())
        self.created_at: float = datetime.now().timestamp()
        self.priority: int = kwargs.get('priority', 5)     # 优先级：1-10，数字越大优先级越高
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'task_id': self.task_id,
            'task_type': 'video_transcode',
            'video_id': self.video_id,
            'raw_file_path': self.raw_file_path,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'quality': self.quality,
            'format': self.format,
            'generate_cover': self.generate_cover,
            'created_at': self.created_at,
            'priority': self.priority,
            'status': 'pending'
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscodeTaskMessage':
        """从字典创建实例"""
        msg = cls(
            video_id=data['video_id'],
            raw_file_path=data['raw_file_path'],
            user_id=data['user_id'],
            title=data.get('title', ''),
            description=data.get('description', ''),
            quality=data.get('quality', '720p'),
            format=data.get('format', 'mp4'),
            generate_cover=data.get('generate_cover', True),
            priority=data.get('priority', 5)
        )
        
        # 设置额外字段
        if 'task_id' in data:
            msg.task_id = data['task_id']
        if 'created_at' in data:
            msg.created_at = data['created_at']
        if 'status' in data:
            msg.status = data['status']
        
        return msg


class KafkaService:
    """
    Kafka业务服务
    封装转码任务的消息队列操作
    """
    
    def __init__(self):
        self.kafka_client = kafka_client
    
    def submit_transcode_task(
        self,
        video_id: int,
        raw_file_path: str,
        user_id: int,
        **kwargs
    ) -> str:
        """
        提交转码任务
        
        Args:
            video_id: 视频ID
            raw_file_path: 原始文件路径
            user_id: 用户ID
            **kwargs: 额外参数
            
        Returns:
            任务ID
        """
        # 创建任务消息
        task_msg = TranscodeTaskMessage(
            video_id=video_id,
            raw_file_path=raw_file_path,
            user_id=user_id,
            **kwargs
        )
        
        # 发送到Kafka
        success = self.kafka_client.send_transcode_task(task_msg.to_dict())
        
        if success:
            print(f"转码任务提交成功 - Task ID: {task_msg.task_id}")
            return task_msg.task_id
        else:
            raise Exception("提交转码任务失败")
    
    def process_transcode_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理转码任务（消费者端调用）
        
        Args:
            task_data: 任务数据
            
        Returns:
            处理结果
        """
        task_msg = TranscodeTaskMessage.from_dict(task_data)
        
        print(f"开始处理转码任务 - Task ID: {task_msg.task_id}, Video ID: {task_msg.video_id}")
        
        try:
            # TODO: 实现实际的转码逻辑
            # 这里先返回模拟结果
            result = {
                'task_id': task_msg.task_id,
                'video_id': task_msg.video_id,
                'status': 'completed',
                'processed_at': datetime.now().timestamp(),
                'output_file': f"transcoded_{task_msg.video_id}.mp4",
                'cover_file': f"cover_{task_msg.video_id}.jpg" if task_msg.generate_cover else None,
                'duration': 120,  # 模拟视频时长
                'file_size': 15728640,  # 模拟文件大小 (15MB)
                'quality': task_msg.quality
            }
            
            print(f"转码任务处理完成 - Task ID: {task_msg.task_id}")
            return result
            
        except Exception as e:
            error_result = {
                'task_id': task_msg.task_id,
                'video_id': task_msg.video_id,
                'status': 'failed',
                'error': str(e),
                'processed_at': datetime.now().timestamp()
            }
            
            print(f"转码任务处理失败 - Task ID: {task_msg.task_id}, Error: {e}")
            return error_result
    
    def start_consumer(self, message_handler: Callable[[Dict[str, Any]], None] = None) -> None:
        """
        启动消息消费者
        
        Args:
            message_handler: 自定义消息处理器（可选）
        """
        if message_handler is None:
            # 使用默认处理器
            message_handler = self.process_transcode_task
        
        print(f"启动Kafka消费者 - Topic: {settings.KAFKA_TRANSCODE_TOPIC}")
        
        try:
            self.kafka_client.consume_messages(message_handler)
        except KeyboardInterrupt:
            print("消费者已停止")
        except Exception as e:
            print(f"消费者发生错误: {e}")
        finally:
            self.kafka_client.close()


# 创建全局服务实例
kafka_service = KafkaService()