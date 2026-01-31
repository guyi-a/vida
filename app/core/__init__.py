# Core module init
from .config import settings
from .dependencies import (
    get_db,
    get_current_user,
    require_admin,
    check_owner_or_admin,
    oauth2_scheme
)
from .exception import (
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    BadRequestException,
    BaseAPIException,
    setup_exception_handlers
)
from .exception_handlers import (
    api_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler,
    http_exception_handler,
    configure_exception_handlers
)
from .middleware import LoggingMiddleware, TimingMiddleware, setup_cors_middleware
from .logging_config import setup_logging

__all__ = [
    "settings",
    "get_db",
    "get_current_user", 
    "require_admin",
    "check_owner_or_admin",
    "oauth2_scheme",
    "UnauthorizedException",
    "ForbiddenException",
    "NotFoundException",
    "BadRequestException",
    "BaseAPIException",
    "api_exception_handler",
    "validation_exception_handler",
    "sqlalchemy_exception_handler",
    "general_exception_handler",
    "http_exception_handler",
    "LoggingMiddleware",
    "TimingMiddleware",
    "setup_cors_middleware",
    "setup_exception_handlers",
    "setup_logging"
]