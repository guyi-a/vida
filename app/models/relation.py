"""
用户关系模型
用户关注关系表
"""

from sqlalchemy import Column, BigInteger, DateTime, text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Relation(Base):
    """
    用户关系模型 - Relations表结构
    
    字段说明：
    - id: 用户关系id（主键，自增）
    - follow_id: 关注的用户id
    - follower_id: 粉丝用户id
    - created_at: 关注时间
    
    注意：这里不设置外键约束，按照要求在业务代码中处理
    通过数据库触发器或业务逻辑维护users表的follow_count和follower_count字段
    """
    
    __tablename__ = "relations"
    
    # 主键，自增
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="用户关系id")
    
    # 关注的用户id (用户A关注了谁)
    follow_id = Column(
        BigInteger,
        nullable=False, 
        comment="关注的用户id"
    )
    
    # 粉丝用户id (谁关注了用户)
    follower_id = Column(
        BigInteger, 
        nullable=False, 
        comment="粉丝用户id"
    )
    
    # 关注时间
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        comment="关注时间"
    )
    
    # 唯一索引，防止重复关注
    __table_args__ = (
        Index("idx_unique_follow_relation", "follow_id", "follower_id", unique=True),
        Index("idx_follower_id", "follower_id"),  # 查询粉丝列表
        Index("idx_follow_id", "follow_id"),       # 查询关注列表
        Index("idx_relations_created_at", "created_at"),    # 按关注时间排序
        {"comment": "用户关系表"}
    )
    
    def __repr__(self):
        """对象的字符串表示"""
        return f"<Relation(id={self.id}, follow_id={self.follow_id}, follower_id={self.follower_id})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "follow_id": self.follow_id,
            "follower_id": self.follower_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }