"""
视频相关 API
提供视频上传、查询、更新、删除等功能
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from io import BytesIO
import time
import uuid

from app.core.dependencies import get_db, get_current_user
from app.core.exception import NotFoundException, BadRequestException
from app.core.config import settings
from app.models.user import User
from app.models.video import Video
from app.crud import video_crud
from app.schemas.response.base_response import BaseResponse, PaginatedResponse
from app.schemas.response.video_response import (
    VideoInfoResponse,
    VideoCreateResponse,
    VideoUpdateResponse,
    VideoDeleteResponse,
    VideoListResponse
)
from app.schemas.request.video_request import (
    VideoCreateRequest,
    VideoUpdateRequest,
    VideoListRequest
)
from app.infra.minio.minio_client import minio_client
from app.infra.kafka.kafka_service import kafka_service


router = APIRouter(prefix="/api/v1/videos", tags=["视频管理"])


def video_to_response(video: Video, include_author: bool = False) -> dict:
    """
    将 Video 模型转换为响应格式
    
    Args:
        video: Video 模型对象
        include_author: 是否包含作者信息
        
    Returns:
        dict: 视频信息字典
    """
    video_dict = {
        "id": video.id,
        "author_id": video.author_id,
        "title": video.title,
        "description": video.description,
        "play_url": video.play_url,
        "cover_url": video.cover_url,
        "duration": video.duration or 0,
        "file_size": video.file_size or 0,
        "file_format": video.file_format,
        "width": video.width,
        "height": video.height,
        "status": video.status,
        "view_count": video.view_count or 0,
        "favorite_count": video.favorite_count or 0,
        "comment_count": video.comment_count or 0,
        "publish_time": video.publish_time,
        "created_at": video.created_at.isoformat() if video.created_at else None,
        "updated_at": video.updated_at.isoformat() if video.updated_at else None
    }
    
    if include_author and video.author:
        video_dict["author"] = {
            "id": video.author.id,
            "username": video.author.user_name,
            "avatar": video.author.avatar
        }
    
    return video_dict


@router.post("/upload", response_model=BaseResponse, summary="上传视频")
async def upload_video(
    video_file: UploadFile = File(..., description="视频文件"),
    title: str = Form(..., min_length=1, max_length=200, description="视频标题"),
    description: Optional[str] = Form(None, description="视频描述"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传视频文件
    
    流程：
    1. 验证文件格式和大小
    2. 上传到 MinIO 原始桶（私有）
    3. 创建视频记录到数据库
    4. 发送 Kafka 转码任务消息
    5. 返回视频ID和上传信息
    """
    try:
        # 1. 验证文件格式
        allowed_formats = ['mp4', 'avi', 'mov', 'mkv', 'flv', 'webm']
        file_ext = video_file.filename.split('.')[-1].lower() if video_file.filename else ''
        if file_ext not in allowed_formats:
            raise BadRequestException(f"不支持的文件格式，支持的格式：{', '.join(allowed_formats)}")
        
        # 2. 验证文件大小（限制 500MB）
        max_size = 500 * 1024 * 1024  # 500MB
        file_content = await video_file.read()
        file_size = len(file_content)
        if file_size > max_size:
            raise BadRequestException(f"文件大小超过限制（最大 {max_size / 1024 / 1024}MB）")
        
        if file_size == 0:
            raise BadRequestException("文件不能为空")
        
        # 3. 上传到 MinIO 原始桶
        object_name = f"user_{current_user.id}/{int(time.time())}_{uuid.uuid4().hex[:8]}_{video_file.filename}"
        
        file_obj = BytesIO(file_content)
        uploaded_name = minio_client.upload_file(
            file_obj=file_obj,
            object_name=object_name,
            bucket_name=settings.MINIO_RAW_BUCKET,
            content_type=video_file.content_type or "video/mp4"
        )
        
        # 4. 创建视频记录
        video_data = {
            "author_id": current_user.id,
            "title": title,
            "description": description,
            "status": "pending",
            "file_size": file_size,
            "file_format": file_ext
        }
        
        video = await video_crud.create(db, video_data)
        
        # 4.5. 同步视频到ES（异步，不阻塞主流程）
        try:
            from app.infra.elasticsearch.sync_service import sync_video_to_es
            author_name = current_user.user_name if current_user else None
            await sync_video_to_es(video, author_name)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"同步视频到ES失败（不影响主流程）: {e}")
        
        # 5. 发送 Kafka 转码任务消息
        try:
            task_id = kafka_service.submit_transcode_task(
                video_id=video.id,
                raw_file_path=uploaded_name,
                user_id=current_user.id,
                title=title,
                description=description or ""
            )
        except Exception as e:
            # Kafka 发送失败不影响视频记录创建，记录日志即可
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"发送转码任务失败: {e}")
            task_id = None
        
        # 6. 获取预签名 URL（用于后续下载）
        presigned_url = minio_client.get_file_url(
            object_name=uploaded_name,
            bucket_name=settings.MINIO_RAW_BUCKET,
            expires=3600  # 1小时有效期
        )
        
        return BaseResponse(
            success=True,
            message="视频上传成功，转码任务已提交",
            data={
                "video_id": video.id,
                "object_name": uploaded_name,
                "upload_url": presigned_url,
                "status": video.status,
                "note": "视频正在转码中，转码完成后将自动发布"
            }
        )
        
    except BadRequestException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"上传视频失败: {str(e)}"
        )


@router.get("/feed", response_model=BaseResponse, summary="获取视频流")
async def get_video_feed(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频流（刷视频）
    
    返回已发布的视频列表，按发布时间倒序排列
    支持分页查询
    不需要登录即可访问
    """
    try:
        skip = (page - 1) * page_size
        
        # 查询已发布的视频（加载作者信息）
        videos = await video_crud.list_videos(
            db=db,
            skip=skip,
            limit=page_size,
            status="published",
            load_author=True
        )
        
        # 获取总数
        total = await video_crud.count_videos(
            db=db,
            status="published"
        )
        
        # 转换为响应格式（包含作者信息）
        video_list = []
        for video in videos:
            # 关联查询作者信息
            if video.author:
                video_dict = video_to_response(video, include_author=True)
            else:
                video_dict = video_to_response(video)
            video_list.append(video_dict)
        
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message="获取视频流成功",
            data={
                "videos": video_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取视频流失败: {str(e)}"
        )


@router.get("/{video_id}", response_model=BaseResponse, summary="获取视频详情")
async def get_video_detail(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频详情
    
    如果视频已发布，会增加观看次数
    需要登录才能访问
    """
    try:
        video = await video_crud.get_by_id(db, video_id, load_author=True)
        if not video:
            raise NotFoundException(f"视频不存在: {video_id}")
        
        # 如果视频已发布，增加观看次数（异步更新）
        if video.status == "published":
            await video_crud.increment_view_count(db, video_id)
            # 重新获取以获取更新后的 view_count
            video = await video_crud.get_by_id(db, video_id, load_author=True)
        
        video_dict = video_to_response(video, include_author=True)
        
        return BaseResponse(
            success=True,
            message="获取视频详情成功",
            data=video_dict
        )
        
    except NotFoundException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取视频详情失败: {str(e)}"
        )


@router.get("/my/list", response_model=BaseResponse, summary="获取我的视频列表")
async def get_my_videos(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的视频列表
    
    需要登录，只能查看自己的视频
    """
    try:
        skip = (page - 1) * page_size
        
        videos = await video_crud.list_videos(
            db=db,
            skip=skip,
            limit=page_size,
            author_id=current_user.id,
            status=status
        )
        
        total = await video_crud.count_videos(
            db=db,
            author_id=current_user.id,
            status=status
        )
        
        video_list = [video_to_response(video) for video in videos]
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message="获取我的视频列表成功",
            data={
                "videos": video_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取我的视频列表失败: {str(e)}"
        )


@router.put("/{video_id}", response_model=BaseResponse, summary="更新视频")
async def update_video(
    video_id: int,
    request: VideoUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新视频信息
    
    只能更新自己发布的视频
    """
    try:
        # 检查视频是否存在且属于当前用户
        video = await video_crud.get_by_id_and_author(db, video_id, current_user.id)
        if not video:
            raise NotFoundException(f"视频不存在或无权限修改: {video_id}")
        
        # 准备更新数据
        update_data = {}
        if request.title is not None:
            update_data["title"] = request.title
        if request.description is not None:
            update_data["description"] = request.description
        if request.status is not None:
            # 验证状态值
            valid_statuses = ["pending", "processing", "published", "failed", "deleted"]
            if request.status not in valid_statuses:
                raise BadRequestException(f"无效的状态值: {request.status}")
            update_data["status"] = request.status
        
        if not update_data:
            raise BadRequestException("没有需要更新的字段")
        
        # 更新视频
        updated_video = await video_crud.update(db, video_id, update_data)
        if not updated_video:
            raise NotFoundException(f"更新失败: {video_id}")
        
        # 同步更新到ES（异步，不阻塞主流程）
        try:
            from app.infra.elasticsearch.sync_service import update_video_in_es
            # 重新加载作者信息
            updated_video = await video_crud.get_by_id(db, video_id, load_author=True)
            if updated_video and updated_video.author:
                author_name = updated_video.author.user_name
                await update_video_in_es(updated_video, author_name)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"同步视频更新到ES失败（不影响主流程）: {e}")
        
        updated_fields = list(update_data.keys())
        
        return BaseResponse(
            success=True,
            message="更新视频成功",
            data={
                "video_id": updated_video.id,
                "updated_fields": updated_fields
            }
        )
        
    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新视频失败: {str(e)}"
        )


@router.delete("/{video_id}", response_model=BaseResponse, summary="删除视频")
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除视频（软删除）
    
    只能删除自己发布的视频
    """
    try:
        # 检查视频是否存在且属于当前用户
        video = await video_crud.get_by_id_and_author(db, video_id, current_user.id)
        if not video:
            raise NotFoundException(f"视频不存在或无权限删除: {video_id}")
        
        # 软删除
        success = await video_crud.delete(db, video_id)
        if not success:
            raise NotFoundException(f"删除失败: {video_id}")
        
        # 从ES删除（异步，不阻塞主流程）
        try:
            from app.infra.elasticsearch.sync_service import delete_video_from_es
            await delete_video_from_es(video_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"从ES删除视频失败（不影响主流程）: {e}")
        
        from datetime import datetime
        return BaseResponse(
            success=True,
            message="删除视频成功",
            data={
                "video_id": video_id,
                "deleted_at": datetime.utcnow().isoformat()
            }
        )
        
    except NotFoundException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除视频失败: {str(e)}"
        )

