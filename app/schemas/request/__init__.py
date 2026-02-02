# Request schemas module init
from .auth_request import LoginRequest, RegisterRequest
from .user_request import UserUpdateRequest
from .video_request import (
    VideoCreateRequest,
    VideoUpdateRequest,
    VideoPublishRequest,
    VideoListRequest
)
from .comment_request import (
    CommentCreateRequest,
    CommentUpdateRequest
)

__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "UserUpdateRequest",
    "VideoCreateRequest",
    "VideoUpdateRequest",
    "VideoPublishRequest",
    "VideoListRequest",
    "CommentCreateRequest",
    "CommentUpdateRequest"
]