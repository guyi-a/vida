



# Response schemas module init
from .auth_response import (
    TokenResponse,
    UserInfoResponse,
    LoginResponse,
    RegisterResponse,
    LogoutResponse
)
from .user_response import (
    UserListResponse,
    UserUpdateResponse,
    PasswordChangeResponse,
    UserDeleteResponse
)
from .base_response import BaseResponse, PaginatedResponse
from .video_response import (
    VideoInfoResponse,
    VideoCreateResponse,
    VideoUpdateResponse,
    VideoDeleteResponse,
    VideoListResponse
)
from .favorite_response import (
    FavoriteInfoResponse,
    FavoriteCreateResponse,
    FavoriteDeleteResponse,
    FavoriteStatusResponse,
    FavoriteListResponse,
    BatchFavoriteStatusResponse
)
from .comment_response import (
    CommentInfoResponse,
    CommentCreateResponse,
    CommentUpdateResponse,
    CommentDeleteResponse,
    CommentListResponse,
    CommentWithRepliesResponse,
    CommentTreeResponse
)
from .relation_response import (
    RelationInfoResponse,
    UserInfoInRelation,
    RelationDetailResponse,
    FollowResponse,
    UnfollowResponse,
    FollowStatusResponse,
    RelationListResponse,
    BatchFollowStatusResponse,
    MutualFollowResponse
)

__all__ = [
    "TokenResponse",
    "UserInfoResponse",
    "LoginResponse",
    "RegisterResponse",
    "LogoutResponse",
    "UserListResponse",
    "UserUpdateResponse",
    "PasswordChangeResponse",
    "UserDeleteResponse",
    "BaseResponse",
    "PaginatedResponse",
    "VideoInfoResponse",
    "VideoCreateResponse",
    "VideoUpdateResponse",
    "VideoDeleteResponse",
    "VideoListResponse",
    "FavoriteInfoResponse",
    "FavoriteCreateResponse",
    "FavoriteDeleteResponse",
    "FavoriteStatusResponse",
    "FavoriteListResponse",
    "BatchFavoriteStatusResponse",
    "CommentInfoResponse",
    "CommentCreateResponse",
    "CommentUpdateResponse",
    "CommentDeleteResponse",
    "CommentListResponse",
    "CommentWithRepliesResponse",
    "CommentTreeResponse",
    "RelationInfoResponse",
    "UserInfoInRelation",
    "RelationDetailResponse",
    "FollowResponse",
    "UnfollowResponse",
    "FollowStatusResponse",
    "RelationListResponse",
    "BatchFollowStatusResponse",
    "MutualFollowResponse"
]



