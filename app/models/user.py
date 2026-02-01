from sqlalchemy import Column, BigInteger, String, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class User(Base):
    """
    用户数据模型 - Users 表结构
    
    字段说明：
    - id: 用户标识（主键，自增）
    - user_name: 用户名
    - password: 密码
    - follow_count: 关注其他用户个数，设有 trigger 根据 relations 表变化
    - follower_count: 粉丝个数，设有 trigger 根据 relations 表变化  
    - total_favorited: 用户被喜欢的视频数量，设有 trigger 根据 favorites 表变化
    - favorite_count: 用户喜欢的视频数量，设有 trigger 根据 favorites 表变化
    - avatar: 用户头像
    - background_image: 主页背景
    - userRole: 用户角色：user/admin（非空，默认值为 user）
    """
    
    __tablename__ = "users"
    
    # 主键，自增
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="用户标识")
    
    # 用户名
    user_name = Column(String(255), nullable=False, unique=True, comment="用户名")
    
    # 密码
    password = Column(String(255), nullable=False, comment="密码")
    
    # 关注其他用户个数（设有 trigger 根据 relations 表变化）
    follow_count = Column(BigInteger, nullable=False, server_default=text("0"), comment="关注其他用户个数")
    
    # 粉丝个数（设有 trigger 根据 relations 表变化）
    follower_count = Column(BigInteger, nullable=False, server_default=text("0"), comment="粉丝个数")
    
    # 用户被喜欢的视频数量（设有 trigger 根据 favorites 表变化）
    total_favorited = Column(BigInteger, nullable=False, server_default=text("0"), comment="用户被喜欢的视频数量")
    
    # 用户喜欢的视频数量（设有 trigger 根据 favorites 表变化）
    favorite_count = Column(BigInteger, nullable=False, server_default=text("0"), comment="用户喜欢的视频数量")
    
    # 用户头像
    avatar = Column(String(500), nullable=True, comment="用户头像")
    
    # 主页背景
    background_image = Column(String(500), nullable=True, comment="主页背景")
    
    # 用户角色：user/admin（非空，默认值为 user）
    userRole = Column(String(256), nullable=False, server_default=text("'user'"), comment="用户角色：user/admin")
    
    # 软删除标识 (0: 未删除, 1: 已删除)
    isDelete = Column(BigInteger, nullable=False, server_default=text("0"), comment="删除标识：0-未删除，1-已删除")
    
    # 关系定义
    videos = relationship("Video", back_populates="author", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, user_name='{self.user_name}', userRole='{self.userRole}')>"
    
    def to_dict(self):
        """转换为字典格式，便于序列化"""
        return {
            "id": self.id,
            "user_name": self.user_name,
            "follow_count": self.follow_count,
            "follower_count": self.follower_count,
            "total_favorited": self.total_favorited,
            "favorite_count": self.favorite_count,
            "avatar": self.avatar,
            "background_image": self.background_image,
            "userRole": self.userRole
        }