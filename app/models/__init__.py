# Models module init
# 导入所有数据模型
from .user import User
from .video import Video
from .favorite import Favorite
from .comment import Comment
from .relation import Relation

# 创建所有表的基础类
from app.db.database import Base

__all__ = [
    "User",
    "Video", 
    "Favorite",
    "Comment",
    "Relation",
    "Base"
]