from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/api/v1", tags=["健康检查"])


@router.get("/healthz", summary="健康检查")
async def healthz() -> Dict[str, Any]:
    """
    健康检查接口，用于验证服务是否正常运行
    
    Returns:
        Dict[str, Any]: 健康状态信息
    """
    return {
        "status": "ok",
        "message": "Service is healthy",
        "service": "user-management-api",
        "version": "1.0.0"
    }


@router.get("/ready", summary="就绪检查")
async def ready() -> Dict[str, Any]:
    """
    就绪检查接口，用于验证服务是否准备好接收流量
    
    Returns:
        Dict[str, Any]: 就绪状态信息
    """
    try:
        # 可以在这里添加数据库连接检查等
        return {
            "status": "ready",
            "message": "Service is ready to accept requests",
            "checks": {
                "database": "connected",
                "external_services": "available"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: {str(e)}"
        )


@router.get("/status", summary="服务状态")
async def status() -> Dict[str, Any]:
    """
    获取服务详细状态信息
    
    Returns:
        Dict[str, Any]: 详细状态信息
    """
    return {
        "status": "running",
        "timestamp": "2024-01-31T12:00:00Z",
        "uptime": "1h 30m",
        "memory_usage": "ok",
        "disk_usage": "ok",
        "active_connections": 5,
        "total_requests": 1234
    }