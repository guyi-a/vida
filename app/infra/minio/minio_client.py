"""
MinIO客户端工具类
提供MinIO对象存储的封装，支持文件上传、下载、删除、URL生成等操作
"""

from minio import Minio
from minio.error import S3Error
from typing import Optional, List, BinaryIO
import mimetypes
import os
from datetime import timedelta

from app.core.config import settings


class MinioClient:
    """
    MinIO客户端封装类
    提供简洁的接口操作MinIO对象存储
    """
    
    def __init__(self):
        """初始化MinIO客户端"""
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        
        # 确保必需的bucket存在
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """确保必需的bucket存在，不存在则创建"""
        buckets = [
            settings.MINIO_RAW_BUCKET, 
            settings.MINIO_PUBLIC_BUCKET,
            settings.MINIO_AVATAR_BUCKET,
            settings.MINIO_BANNER_BUCKET
        ]
        
        for bucket_name in buckets:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                print(f"创建bucket: {bucket_name}")
            else:
                print(f"bucket已存在: {bucket_name}")
    
    def upload_file(
        self, 
        file_obj: BinaryIO, 
        object_name: str, 
        bucket_name: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        上传文件到MinIO
        
        Args:
            file_obj: 文件对象（二进制模式）
            object_name: 对象名称（在bucket中的路径）
            bucket_name: bucket名称
            content_type: 文件内容类型
            metadata: 元数据
            
        Returns:
            对象名称
        """
        try:
            # 获取文件大小
            file_obj.seek(0, os.SEEK_END)
            file_size = file_obj.tell()
            file_obj.seek(0)
            
            # 自动检测content_type
            if content_type is None:
                content_type, _ = mimetypes.guess_type(object_name)
                if content_type is None:
                    content_type = "application/octet-stream"
            
            # 上传文件
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=file_obj,
                length=file_size,
                content_type=content_type,
                metadata=metadata
            )
            
            return object_name
            
        except S3Error as e:
            raise Exception(f"上传文件失败: {e}")
    
    def download_file(
        self, 
        object_name: str, 
        bucket_name: str, 
        file_path: str
    ) -> None:
        """
        从MinIO下载文件
        
        Args:
            object_name: 对象名称
            bucket_name: bucket名称
            file_path: 本地文件保存路径
        """
        try:
            self.client.fget_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path
            )
        except S3Error as e:
            raise Exception(f"下载文件失败: {e}")
    
    def get_object_data(
        self, 
        object_name: str, 
        bucket_name: str
    ) -> bytes:
        """
        获取对象数据
        
        Args:
            object_name: 对象名称
            bucket_name: bucket名称
            
        Returns:
            文件数据
        """
        try:
            response = self.client.get_object(
                bucket_name=bucket_name,
                object_name=object_name
            )
            return response.read()
            
        except S3Error as e:
            raise Exception(f"获取对象数据失败: {e}")
        finally:
            if 'response' in locals():
                response.close()
                response.release_conn()
    
    def delete_file(
        self, 
        object_name: str, 
        bucket_name: str
    ) -> None:
        """
        删除文件
        
        Args:
            object_name: 对象名称
            bucket_name: bucket名称
        """
        try:
            self.client.remove_object(
                bucket_name=bucket_name,
                object_name=object_name
            )
        except S3Error as e:
            raise Exception(f"删除文件失败: {e}")
    
    def get_file_url(
        self, 
        object_name: str, 
        bucket_name: str, 
        expires: int = 3600
    ) -> str:
        """
        生成文件的预签名URL
        
        Args:
            object_name: 对象名称
            bucket_name: bucket名称
            expires: URL过期时间（秒）
            
        Returns:
            预签名URL
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            raise Exception(f"生成URL失败: {e}")
    
    def file_exists(
        self, 
        object_name: str, 
        bucket_name: str
    ) -> bool:
        """
        检查文件是否存在
        
        Args:
            object_name: 对象名称
            bucket_name: bucket名称
            
        Returns:
            是否存在
        """
        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def list_files(
        self, 
        bucket_name: str, 
        prefix: Optional[str] = None
    ) -> List[str]:
        """
        列出bucket中的文件
        
        Args:
            bucket_name: bucket名称
            prefix: 前缀过滤
            
        Returns:
            文件名列表
        """
        try:
            objects = self.client.list_objects(
                bucket_name=bucket_name,
                prefix=prefix
            )
            return [obj.object_name for obj in objects]
        except S3Error as e:
            raise Exception(f"列出文件失败: {e}")
    
    def get_public_url(
        self, 
        object_name: str,
        bucket_name: str = None
    ) -> str:
        """
        获取公共bucket中对象的直接访问URL
        
        Args:
            object_name: 对象名称
            bucket_name: bucket名称（默认为public-videos）
            
        Returns:
            直接访问URL
        """
        if bucket_name is None:
            bucket_name = settings.MINIO_PUBLIC_BUCKET
            
        return f"http://{settings.MINIO_ENDPOINT}/{bucket_name}/{object_name}"


# 创建全局MinIO客户端实例
minio_client = MinioClient()