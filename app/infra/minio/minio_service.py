"""
MinIO服务层
封装MinIO的各种业务操作，提供更高级的接口
"""

from typing import BinaryIO, Optional
import uuid
import os
from datetime import datetime

from app.core.config import settings
from .minio_client import minio_client


class MinioService:
    """
    MinIO服务层
    提供基于业务场景的MinIO操作接口
    """
    
    @staticmethod
    def generate_video_filename(original_filename: str) -> str:
        """
        生成视频文件名
        
        Args:
            original_filename: 原始文件名
            
        Returns:
            生成的文件名
        """
        ext = os.path.splitext(original_filename)[1]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"video_{timestamp}_{unique_id}{ext}"
    
    @staticmethod
    def generate_image_filename(original_filename: str, prefix: str = "image") -> str:
        """
        生成图片文件名
        
        Args:
            original_filename: 原始文件名
            prefix: 前缀
            
        Returns:
            生成的文件名
        """
        ext = os.path.splitext(original_filename)[1]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}_{timestamp}_{unique_id}{ext}"
    
    @classmethod
    def upload_video(
        cls,
        file_obj: BinaryIO,
        filename: str,
        user_id: int
    ) -> dict:
        """
        上传视频到原始桶（私有）
        
        Args:
            file_obj: 文件对象
            filename: 原始文件名
            user_id: 用户ID
            
        Returns:
            dict包含上传结果
        """
        # 生成唯一文件名
        object_name = f"user_{user_id}/{cls.generate_video_filename(filename)}"
        
        # 上传到原始桶
        minio_client.upload_file(
            file_obj=file_obj,
            object_name=object_name,
            bucket_name=settings.MINIO_RAW_BUCKET,
            content_type="video/mp4"
        )
        
        return {
            "object_name": object_name,
            "bucket": settings.MINIO_RAW_BUCKET,
            "upload_url": minio_client.get_file_url(
                object_name=object_name,
                bucket_name=settings.MINIO_RAW_BUCKET
            )
        }
    
    @classmethod
    def upload_video_cover(
        cls,
        file_obj: BinaryIO,
        filename: str,
        user_id: int,
        video_object_name: str
    ) -> dict:
        """
        上传视频封面到公共桶
        
        Args:
            file_obj: 文件对象
            filename: 原始文件名
            user_id: 用户ID
            video_object_name: 视频对象名称
            
        Returns:
            dict包含上传结果
        """
        # 基于视频文件名生成封面文件名
        video_name = os.path.splitext(video_object_name)[0]
        object_name = f"{video_name}_cover{os.path.splitext(filename)[1]}"
        
        # 上传到公共桶
        minio_client.upload_file(
            file_obj=file_obj,
            object_name=object_name,
            bucket_name=settings.MINIO_PUBLIC_BUCKET,
            content_type="image/jpeg"
        )
        
        return {
            "object_name": object_name,
            "bucket": settings.MINIO_PUBLIC_BUCKET,
            "public_url": minio_client.get_public_url(object_name)
        }
    
    @classmethod
    def publish_video(
        cls,
        file_obj: BinaryIO,
        filename: str,
        user_id: int
    ) -> dict:
        """
        发布已转码的视频到公共桶
        
        Args:
            file_obj: 转码后的视频文件
            filename: 文件名
            user_id: 用户ID
            
        Returns:
            dict包含发布结果
        """
        object_name = f"user_{user_id}/{cls.generate_video_filename(filename)}"
        
        # 上传到公共桶
        minio_client.upload_file(
            file_obj=file_obj,
            object_name=object_name,
            bucket_name=settings.MINIO_PUBLIC_BUCKET,
            content_type="video/mp4"
        )
        
        return {
            "object_name": object_name,
            "bucket": settings.MINIO_PUBLIC_BUCKET,
            "public_url": minio_client.get_public_url(object_name)
        }
    
    @classmethod
    def upload_user_avatar(
        cls,
        file_obj: BinaryIO,
        filename: str,
        user_id: int
    ) -> dict:
        """
        上传用户头像
        
        Args:
            file_obj: 文件对象
            filename: 原始文件名
            user_id: 用户ID
            
        Returns:
            dict包含上传结果
        """
        object_name = f"user_{user_id}{os.path.splitext(filename)[1]}"
        
        # 上传到用户头像专用桶
        minio_client.upload_file(
            file_obj=file_obj,
            object_name=object_name,
            bucket_name=settings.MINIO_AVATAR_BUCKET,
            content_type="image/jpeg"
        )
        
        return {
            "object_name": object_name,
            "bucket": settings.MINIO_AVATAR_BUCKET,
            "public_url": minio_client.get_public_url(object_name, settings.MINIO_AVATAR_BUCKET)
        }
    
    @classmethod
    def upload_user_banner(
        cls,
        file_obj: BinaryIO,
        filename: str,
        user_id: int
    ) -> dict:
        """
        上传用户主页背景
        
        Args:
            file_obj: 文件对象
            filename: 原始文件名
            user_id: 用户ID
            
        Returns:
            dict包含上传结果
        """
        object_name = f"user_{user_id}{os.path.splitext(filename)[1]}"
        
        # 上传到用户背景专用桶
        minio_client.upload_file(
            file_obj=file_obj,
            object_name=object_name,
            bucket_name=settings.MINIO_BANNER_BUCKET,
            content_type="image/jpeg"
        )
        
        return {
            "object_name": object_name,
            "bucket": settings.MINIO_BANNER_BUCKET,
            "public_url": minio_client.get_public_url(object_name, settings.MINIO_BANNER_BUCKET)
        }
    
    @classmethod
    def delete_video(
        cls,
        object_name: str,
        user_id: int
    ) -> None:
        """
        删除视频（包括原始和转码后）
        
        Args:
            object_name: 对象名称
            user_id: 用户ID
        """
        # 删除原始视频
        try:
            minio_client.delete_file(
                object_name=object_name,
                bucket_name=settings.MINIO_RAW_BUCKET
            )
        except Exception:
            pass  # 原始文件可能不存在
        
        # 删除转码后的视频
        try:
            minio_client.delete_file(
                object_name=object_name,
                bucket_name=settings.MINIO_PUBLIC_BUCKET
            )
        except Exception:
            pass
        
        # 删除封面
        try:
            cover_name = f"{os.path.splitext(object_name)[0]}_cover.jpg"
            minio_client.delete_file(
                object_name=cover_name,
                bucket_name=settings.MINIO_PUBLIC_BUCKET
            )
        except Exception:
            pass
    
    @classmethod
    def get_video_url(
        cls,
        object_name: str,
        user_id: int,
        expires: int = 3600
    ) -> str:
        """
        获取视频播放URL
        
        Args:
            object_name: 对象名称
            user_id: 用户ID
            expires: 过期时间
            
        Returns:
            视频播放URL
        """
        # 优先从公共桶获取
        if minio_client.file_exists(object_name, settings.MINIO_PUBLIC_BUCKET):
            return minio_client.get_public_url(object_name)
        else:
            # 如果公共桶不存在，从原始桶获取临时URL
            return minio_client.get_file_url(
                object_name=object_name,
                bucket_name=settings.MINIO_RAW_BUCKET,
                expires=expires
            )


# 创建全局服务实例
minio_service = MinioService()