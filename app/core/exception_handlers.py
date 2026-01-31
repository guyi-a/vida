# ==================== 异常处理器 ====================

import logging
from typing import Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from .exception import BaseAPIException


# 配置日志
logger = logging.getLogger(__name__)


async def api_exception_handler(request: Request, exc: BaseAPIException):
    """
    处理自定义API异常
    """
    logger.error(f"API Exception: {exc.message} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.message,
                "type": exc.__class__.__name__
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    处理请求参数验证异常
    """
    logger.error(f"Validation Error: {exc.errors()} - Path: {request.url.path}")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": 422,
                "message": "请求参数验证失败",
                "details": exc.errors(),
                "type": "ValidationError"
            }
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    处理数据库异常
    """
    logger.error(f"Database Error: {str(exc)} - Path: {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "数据库操作失败",
                "type": "DatabaseError"
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    处理其他未捕获的异常
    """
    logger.error(f"Unhandled Exception: {str(exc)} - Path: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "服务器内部错误",
                "type": "InternalServerError"
            }
        }
    )


async def http_exception_handler(request: Request, exc):
    """
    处理HTTP异常
    """
    logger.error(f"HTTP Exception: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "HTTPError"
            }
        }
    )


# ==================== 异常处理器配置 ====================


def configure_exception_handlers(app) -> None:
    """
    配置应用的所有异常处理器
    
    Args:
        app: FastAPI应用实例
    """
    
    # 1. 自定义API异常处理器
    app.add_exception_handler(BaseAPIException, api_exception_handler)
    
    # 2. 请求参数验证异常处理器
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # 3. 数据库异常处理器
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # 4. HTTP异常处理器
    app.add_exception_handler(HTTPException, http_exception_handler)
    
    # 5. 通用异常处理器（捕获其他未处理的异常）
    app.add_exception_handler(Exception, general_exception_handler)