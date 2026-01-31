import time
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings


# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, "INFO"))  # 设置默认日志级别


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    日志输出中间件
    记录请求和响应信息
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录请求信息
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        logger.info(
            f"Request: {request.method} {request.url.path} - "
            f"Client: {client_ip} - "
            f"Query: {dict(request.query_params)}"
        )
        
        # 处理请求
        response = await call_next(request)
        
        # 记录响应信息
        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.4f}s"
        )
        
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """
    耗时记录中间件
    记录每个请求的处理时间
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response


def setup_cors_middleware(app):
    """
    设置跨域中间件
    使用 FastAPI 的 CORSMiddleware
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )