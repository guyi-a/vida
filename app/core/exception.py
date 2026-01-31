from fastapi import HTTPException, status
from typing import Optional


class BaseAPIException(HTTPException):
    """基础API异常类"""
    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[str] = None
    ):
        super().__init__(status_code=status_code, detail=detail or message)
        self.message = message


class UnauthorizedException(BaseAPIException):
    """未授权异常 (401)"""
    def __init__(self, message: str = "认证失败，请先登录"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenException(BaseAPIException):
    """禁止访问异常 (403)"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundException(BaseAPIException):
    """资源不存在异常 (404)"""
    def __init__(self, message: str = "请求的资源不存在"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )




class BadRequestException(BaseAPIException):
    """错误请求异常 (400)"""
    def __init__(self, message: str = "请求参数错误"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )


def setup_exception_handlers(app):
    """
    设置异常处理器
    """
    from app.core.exception_handlers import configure_exception_handlers
    configure_exception_handlers(app)