"""
视频模型
核心视频表结构
"""

from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, text, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Video(Base):
    """
    视频模型 - Videos表结构
    
    字段说明：
    - id: 视频标识（主键，自增）
    - author_id: 视频作者ID
    - title: 视频标题
    - description: 视频描述
    - play_url: 视频播放地址
    - cover_url: 视频封面地址
    - duration: 视频时长（秒）
    - file_size: 文件大小（字节）
    - file_format: 文件格式
    - width: 视频宽度
    - height: 视频高度
    - status: 视频状态
    - view_count: 播放量
    - favorite_count: 点赞数
    - comment_count: 评论数
    - publish_time: 发布时间
    - created_at: 创建时间
    - updated_at: 更新时间
    """
    
    __tablename__ = "videos"
    
    # 主键，自增
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="视频标识")
    
    # 视频作者ID，外键到users表
    author_id = Column(
        BigInteger, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        comment="视频作者ID"
    )
    
    # 视频标题
    title = Column(String(200), nullable=False, comment="视频标题")
    
    # 视频描述
    description = Column(Text, comment="视频描述")
    
    # 视频播放地址
    play_url = Column(String(500), comment="视频播放地址")
    
    # 视频封面地址
    cover_url = Column(String(500), comment="视频封面地址")
    
    # 视频基本信息
    duration = Column(Integer, default=0, comment="视频时长（秒）")
    file_size = Column(BigInteger, default=0, comment="文件大小（字节）")
    file_format = Column(String(20), comment="文件格式")
    width = Column(Integer, comment="视频宽度")
    height = Column(Integer, comment="视频高度")
    
    # 视频状态：pending-待转码，processing-转码中，published-已发布，failed-转码失败，deleted-已删除
    status = Column(String(20), default="pending", comment="视频状态")
    
    # 统计数据
    view_count = Column(BigInteger, default=0, comment="播放量")
    favorite_count = Column(BigInteger, default=0, comment="点赞数")
    comment_count = Column(BigInteger, default=0, comment="评论数")
    
    # 发布时间（Unix时间戳）
    publish_time = Column(BigInteger, comment="发布时间")
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        comment="创建时间"
    )
    
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        comment="更新时间"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_author_id", "author_id"),  # 查询作者的视频
        Index("idx_status", "status"),  # 查询特定状态的视频
        Index("idx_publish_time", "publish_time"),  # 按发布时间排序
        Index("idx_videos_created_at", "created_at"),  # 按创建时间排序
        Index("idx_composite_author_status", "author_id", "status"),  # 复合索引
        {"comment": "视频表"}
    )
    
    # 关系定义
    author = relationship("User", back_populates="videos")
    favorites = relationship("Favorite", back_populates="video", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="video", cascade="all, delete-orphan")
    
    def __repr__(self):
        """对象的字符串表示"""
        return f"<Video(id={self.id}, title='{self.title}', author_id={self.author_id})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "author_id": self.author_id,
            "title": self.title,
            "description": self.description,
            "play_url": self.play_url,
            "cover_url": self.cover_url,
            "duration": self.duration,
            "file_size": self.file_size,
            "file_format": self.file_format,
            "width": self.width,
            "height": self.height,
            "status": self.status,
            "view_count": self.view_count,
            "favorite_count": self.favorite_count,
            "comment_count": self.comment_count,
            "publish_time": self.publish_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }