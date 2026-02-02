# CRUD module init
from .user_crud import user_crud, UserCRUD
from .video_crud import video_crud, VideoCRUD
from .favorite_crud import favorite_crud, FavoriteCRUD
from .comment_crud import comment_crud, CommentCRUD
from .relation_crud import relation_crud, RelationCRUD

__all__ = ["user_crud", "UserCRUD", "video_crud", "VideoCRUD", "favorite_crud", "FavoriteCRUD", "comment_crud", "CommentCRUD", "relation_crud", "RelationCRUD"]