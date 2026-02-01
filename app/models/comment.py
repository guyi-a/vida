"""
评论模型
用户视频评论表
"""

from sqlalchemy import Column, BigInteger, Text, DateTime, text, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Comment(Base):
    """
    评论模型 - Comments表结构
    
    字段说明：
    - id: 评论ID（主键，自增）
    - user_id: 评论用户ID
    - video_id: 被评论视频ID
    - content: 评论内容
    - parent_id: 父评论ID（用于回复功能）
    - like_count: 评论点赞数
    - created_at: 评论时间
    - updated_at: 更新时间
    
    功能：
    - 支持评论回复（通过parent_id实现）
    - 评论点赞统计
    - 层级结构查询
    """
    
    __tablename__ = "comments"
    
    # 主键，自增
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="评论ID")
    
    # 评论用户ID，外键到users表
    user_id = Column(
        BigInteger, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        comment="评论用户ID"
    )
    
    # 被评论视频ID，外键到videos表
    video_id = Column(
        BigInteger, 
        ForeignKey("videos.id", ondelete="CASCADE"), 
        nullable=False, 
        comment="被评论视频ID"
    )
    
    # 评论内容
    content = Column(Text, nullable=False, comment="评论内容")
    
    # 父评论ID，用于回复功能（NULL表示是顶级评论）
    parent_id = Column(
        BigInteger, 
        ForeignKey("comments.id", ondelete="CASCADE"), 
        comment="父评论ID"
    )
    
    # 评论点赞数
    like_count = Column(BigInteger, default=0, comment="评论点赞数")
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        comment="评论时间"
    )
    
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        comment="更新时间"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_comments_user_id", "user_id"),  # 查询用户的评论
        Index("idx_comments_video_id", "video_id"),  # 查询视频的评论
        Index("idx_comments_parent_id", "parent_id"),  # 查询回复的评论
        Index("idx_comments_created_at", "created_at"),  # 按时间排序
        Index("idx_composite_video_created", "video_id", "created_at"),  # 视频评论按时间排序
        {"comment": "用户视频评论表"}
    )
    
    # 关系定义
    user = relationship("User", back_populates="comments")
    video = relationship("Video", back_populates="comments")
    
    # 父评论关系
    parent = relationship("Comment", remote_side=[id], back_populates="replies")
    
    # 回复关댓글들
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")
    
    def __repr__(self):
        """对象的字符串表示"""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Comment(id={self.id}, user_id={self.user_id}, video_id={self.video_id}, content='{content_preview}')>"
    
    def to_dict(self, include_replies: bool = False):
        """转换为字典"""
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "video_id": self.video_id,
            "content": self.content,
            "parent_id": self.parent_id,
            "like_count": self.like_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_replies:
            result["replies"] = [reply.to_dict() for reply in self.replies]
        
        return result
    
    @property
    def is_top_level(self) -> bool:
        """判断是否为顶级评论"""
        return self.parent_id is None
    
    @property
    def replies_count(self) -> int:
        """获取回复数量"""
        return len(self.replies) if self.replies else 0