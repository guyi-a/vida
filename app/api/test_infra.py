"""
基础设施测试接口
用于测试 MinIO、Kafka、Celery 等基础设施组件
"""

from fastapi import APIRouter, UploadFile, File, Body, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.response.base_response import BaseResponse

router = APIRouter(prefix="/api/test/infra", tags=["Infrastructure Test"])


@router.post("/minio/upload")
async def test_minio_upload(file: UploadFile = File(...)):
    """
    测试 MinIO 文件上传功能
    
    上传任意文件到 MinIO 的 raw-videos bucket（原始桶），用于测试 MinIO 连接和上传功能
    """
    try:
        # 直接导入 MinioClient 类并实例化，避免通过 app.infra 包导入
        from app.infra.minio.minio_client import MinioClient
        minio_client = MinioClient()
        
        # 读取文件内容
        file_content = await file.read()
        
        # 生成对象名称
        import time
        import uuid
        object_name = f"test/{int(time.time())}_{uuid.uuid4().hex[:8]}_{file.filename}"
        
        # 上传到原始桶（私有桶）
        from io import BytesIO
        file_obj = BytesIO(file_content)
        
        uploaded_name = minio_client.upload_file(
            file_obj=file_obj,
            object_name=object_name,
            bucket_name=settings.MINIO_RAW_BUCKET,
            content_type=file.content_type
        )
        
        # 获取预签名 URL（私有桶需要使用预签名 URL）
        presigned_url = minio_client.get_file_url(
            object_name=uploaded_name,
            bucket_name=settings.MINIO_RAW_BUCKET,
            expires=3600  # 1小时有效期
        )
        
        return JSONResponse(
            content={
                "success": True,
                "message": "文件上传成功",
                "data": {
                    "filename": file.filename,
                    "object_name": uploaded_name,
                    "bucket": settings.MINIO_RAW_BUCKET,
                    "presigned_url": presigned_url,
                    "file_size": len(file_content),
                    "content_type": file.content_type,
                    "note": "这是私有桶，需要使用预签名 URL 访问"
                }
            },
            status_code=200
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": f"文件上传失败: {str(e)}",
                "error": str(e)
            },
            status_code=500
        )


@router.get("/minio/buckets")
async def test_minio_buckets():
    """
    测试 MinIO bucket 列表
    查看所有可用的 bucket
    """
    try:
        # 直接导入 MinioClient 类并实例化，避免通过 app.infra 包导入
        from app.infra.minio.minio_client import MinioClient
        minio_client = MinioClient()
        
        # 列出所有 bucket
        buckets = minio_client.client.list_buckets()
        bucket_list = []
        for bucket in buckets:
            bucket_list.append({
                "name": bucket.name,
                "creation_date": bucket.creation_date.isoformat() if bucket.creation_date else None
            })
        
        return JSONResponse(
            content={
                "success": True,
                "message": "获取 bucket 列表成功",
                "data": {
                    "buckets": bucket_list,
                    "count": len(bucket_list)
                }
            },
            status_code=200
        )
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return JSONResponse(
            content={
                "success": False,
                "message": f"获取 bucket 列表失败: {str(e)}",
                "error": str(e),
                "detail": error_detail
            },
            status_code=500
        )


@router.get("/minio/raw-bucket-contents")
async def test_minio_raw_bucket_contents():
    """
    测试 MinIO raw bucket 内容列表
    查看 raw-videos 桶中的所有文件内容
    """
    try:
        # 直接导入 MinioClient 类并实例化，避免通过 app.infra 包导入
        from app.infra.minio.minio_client import MinioClient
        minio_client = MinioClient()
        
        # 列出 raw bucket 中的所有对象
        objects = minio_client.client.list_objects(bucket_name=settings.MINIO_RAW_BUCKET, recursive=True)
        
        # 获取更详细的信息
        file_details = []
        for obj in objects:
            # 跳过目录（文件夹），只处理实际的文件
            if obj.object_name.endswith('/'):
                continue
                
            try:
                # 获取对象统计信息
                obj_stat = minio_client.client.stat_object(settings.MINIO_RAW_BUCKET, obj.object_name)
                file_details.append({
                    "object_name": obj.object_name,
                    "size": obj_stat.size,
                    "content_type": obj_stat.content_type,
                    "last_modified": obj_stat.last_modified.isoformat() if obj_stat.last_modified else None,
                    "etag": obj_stat.etag
                })
            except Exception as e:
                # 如果无法获取详细信息，至少添加文件名
                file_details.append({
                    "object_name": obj.object_name,
                    "size": None,
                    "content_type": None,
                    "last_modified": None,
                    "etag": None,
                    "error": str(e)
                })
        
        return JSONResponse(
            content={
                "success": True,
                "message": "获取 raw bucket 内容成功",
                "data": {
                    "bucket": settings.MINIO_RAW_BUCKET,
                    "files": file_details,
                    "count": len(file_details)
                }
            },
            status_code=200
        )
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return JSONResponse(
            content={
                "success": False,
                "message": f"获取 raw bucket 内容失败: {str(e)}",
                "error": str(e),
                "detail": error_detail
            },
            status_code=500
        )


@router.get("/public-bucket", response_model=BaseResponse, summary="获取公开桶文件列表")
async def get_public_bucket_files(
    prefix: Optional[str] = Query(None, description="文件前缀过滤"),
    current_user: User = Depends(get_current_user)
):
    """
    获取公开桶中的文件列表
    
    获取 MinIO 公开桶中的视频文件列表，主要用于管理界面
    需要登录权限
    """
    try:
        # 直接导入 MinioClient 类并实例化
        from app.infra.minio.minio_client import MinioClient
        minio_client = MinioClient()
        
        # 列出 Public bucket 中的所有文件
        files = minio_client.list_files(
            bucket_name=settings.MINIO_PUBLIC_BUCKET,
            prefix=prefix
        )
        
        # 过滤视频文件（支持的格式）
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']
        
        file_list = []
        for file_name in files:
            # 跳过目录
            if file_name.endswith('/'):
                continue
                
            try:
                # 获取文件信息
                file_stat = minio_client.client.stat_object(
                    settings.MINIO_PUBLIC_BUCKET, 
                    file_name
                )
                
                # 确定是否为视频文件
                file_ext = '.' + file_name.split('.')[-1].lower() if '.' in file_name else ''
                is_video = file_ext in video_extensions
                
                # 生成公共访问URL
                public_url = minio_client.get_public_url(file_name)
                
                file_info = {
                    "filename": file_name,
                    "url": public_url,
                    "size": file_stat.size,
                    "content_type": file_stat.content_type,
                    "last_modified": file_stat.last_modified.isoformat() if file_stat.last_modified else None,
                    "is_video": is_video,
                    "file_extension": file_ext
                }
                
                file_list.append(file_info)
                
            except Exception as e:
                # 如果无法获取文件信息，跳过该文件
                file_list.append({
                    "filename": file_name,
                    "url": None,
                    "size": None,
                    "content_type": None,
                    "last_modified": None,
                    "is_video": False,
                    "file_extension": None,
                    "error": str(e)
                })
        
        # 按视频文件和普通文件分类
        video_files = [f for f in file_list if f.get('is_video', False)]
        other_files = [f for f in file_list if not f.get('is_video', False)]
        
        return BaseResponse(
            success=True,
            message=f"获取公开桶文件列表成功，共找到 {len(file_list)} 个文件（{len(video_files)} 个视频）",
            data={
                "bucket": settings.MINIO_PUBLIC_BUCKET,
                "total_files": len(file_list),
                "video_files": video_files,
                "other_files": other_files,
                "video_extensions_supported": video_extensions,
                "video_files_count": len(video_files),
                "other_files_count": len(other_files)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取公开桶文件列表失败: {str(e)}"
        )




