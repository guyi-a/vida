"""
基础设施测试接口
用于测试 MinIO、Kafka、Celery 等基础设施组件
"""

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from app.core.config import settings

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

