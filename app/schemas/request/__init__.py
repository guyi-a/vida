# Request schemas module init
from .auth_request import LoginRequest, RegisterRequest
from .user_request import UserUpdateRequest

__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "UserUpdateRequest"
]