"""
点赞模型
用户视频点赞表
"""

from sqlalchemy import Column, BigInteger, DateTime, text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Favorite(Base):
    """
    点赞模型 - Favorites表结构
    
    字段说明：
    - id: 点赞记录ID（主键，自增）
    - user_id: 点赞用户ID
    - video_id: 被点赞视频ID
    - created_at: 点赞时间
    
    约束：
    - 唯一约束：确保用户对同一视频只能点赞一次
    - 外键约束：关联用户和视频表
    """
    
    __tablename__ = "favorites"
    
    # 主键，自增
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="点赞记录ID")
    
    # 点赞用户ID，外键到users表
    user_id = Column(
        BigInteger, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        comment="点赞用户ID"
    )
    
    # 被点赞视频ID，外键到videos表
    video_id = Column(
        BigInteger, 
        ForeignKey("videos.id", ondelete="CASCADE"), 
        nullable=False, 
        comment="被点赞视频ID"
    )
    
    # 点赞时间
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        comment="点赞时间"
    )
    
    # 唯一约束：防止重复点赞
    __table_args__ = (
        UniqueConstraint('user_id', 'video_id', name='uq_user_video_favorite'),
        Index("idx_favorites_user_id", "user_id"),  # 查询用户的点赞记录
        Index("idx_favorites_video_id", "video_id"),  # 查询视频的点赞记录
        Index("idx_favorites_created_at", "created_at"),  # 按点赞时间排序
        {"comment": "用户视频点赞表"}
    )
    
    # 关系定义
    user = relationship("User", back_populates="favorites")
    video = relationship("Video", back_populates="favorites")
    
    def __repr__(self):
        """对象的字符串表示"""
        return f"<Favorite(id={self.id}, user_id={self.user_id}, video_id={self.video_id})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "video_id": self.video_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }