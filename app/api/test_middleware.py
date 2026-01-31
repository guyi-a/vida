from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.core.exception import UnauthorizedException, ForbiddenException
from app.models.user import User

router = APIRouter(prefix="/api/test", tags=["Middleware Test"])


@router.get("/middleware")
async def test_middleware():
    """
    测试中间件是否正常工作的端点
    应该会记录请求日志，添加安全头等
    """
    return JSONResponse(
        content={
            "message": "Middleware test successful",
            "request_id": "Check headers for X-Request-ID"
        },
        status_code=200
    )


@router.get("/exception")
async def test_exception():
    """
    测试异常处理器是否正常工作的端点
    """
    raise UnauthorizedException("This is a test exception")


@router.get("/validation-error")
async def test_validation_error():
    """
    测试验证错误异常处理器
    """
    # 强制创建一个验证错误
    from pydantic import ValidationError
    raise ValidationError.from_exception_data("test", [])


@router.get("/rate-limit")
async def test_rate_limit():
    """
    测试速率限制
    """
    return JSONResponse(
        content={
            "message": "Rate limit test",
            "info": "Make multiple requests within 1 minute to test rate limiting"
        },
        status_code=200
    )


@router.get("/admin-only")
async def test_admin_only():
    """
    测试管理员权限
    """
    raise ForbiddenException("Admin access required for this endpoint")