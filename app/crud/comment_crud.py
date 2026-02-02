"""
评论 CRUD 操作
提供用户发布评论、删除评论、查询评论等功能
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete, update
from sqlalchemy.orm import joinedload
from typing import Optional, List, Dict, Any
from app.models.comment import Comment
from app.models.video import Video


class CommentCRUD:
    """
    评论 CRUD 操作类
    """
    
    async def create(
        self, 
        db: AsyncSession, 
        user_id: int, 
        video_id: int, 
        content: str,
        parent_id: Optional[int] = None
    ) -> Comment:
        """
        创建评论
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            video_id: 视频ID
            content: 评论内容
            parent_id: 父评论ID（可选，用于回复）
            
        Returns:
            Comment: 创建的评论对象
            
        Raises:
            Exception: 如果数据异常会抛出数据库异常
        """
        comment = Comment(
            user_id=user_id,
            video_id=video_id,
            content=content,
            parent_id=parent_id
        )
        db.add(comment)
        await db.flush()
        await db.refresh(comment)
        return comment
    
    async def delete(self, db: AsyncSession, comment_id: int, user_id: int) -> bool:
        """
        删除评论（只能删除自己的评论）
        
        Args:
            db: 数据库会话
            comment_id: 评论ID
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
        """
        query = delete(Comment).where(
            and_(Comment.id == comment_id, Comment.user_id == user_id)
        )
        result = await db.execute(query)
        return result.rowcount > 0
    
    async def update(
        self, 
        db: AsyncSession, 
        comment_id: int, 
        user_id: int,
        content: str
    ) -> Optional[Comment]:
        """
        更新评论（只能更新自己的评论）
        
        Args:
            db: 数据库会话
            comment_id: 评论ID
            user_id: 用户ID
            content: 新的评论内容
            
        Returns:
            Optional[Comment]: 更新后的评论对象，如果不存在或无权限返回None
        """
        query = update(Comment).where(
            and_(Comment.id == comment_id, Comment.user_id == user_id)
        ).values(content=content)
        result = await db.execute(query)
        
        if result.rowcount > 0:
            # 重新获取更新后的评论
            return await self.get_by_id(db, comment_id)
        return None
    
    async def get_by_id(
        self, 
        db: AsyncSession, 
        comment_id: int, 
        load_user: bool = False,
        load_video: bool = False,
        load_replies: bool = False
    ) -> Optional[Comment]:
        """
        根据ID获取评论
        
        Args:
            db: 数据库会话
            comment_id: 评论ID
            load_user: 是否加载用户信息
            load_video: 是否加载视频信息
            load_replies: 是否加载回复列表
            
        Returns:
            Optional[Comment]: 评论对象，如果不存在返回None
        """
        query = select(Comment).where(Comment.id == comment_id)
        
        if load_user:
            query = query.options(joinedload(Comment.user))
        if load_video:
            query = query.options(joinedload(Comment.video))
        if load_replies:
            query = query.options(joinedload(Comment.replies))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_video(
        self, 
        db: AsyncSession, 
        video_id: int, 
        skip: int = 0, 
        limit: int = 20,
        parent_id: Optional[int] = None,
        load_user: bool = True
    ) -> List[Comment]:
        """
        获取视频的评论列表
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            skip: 跳过数量
            limit: 返回数量限制
            parent_id: 父评论ID（None表示获取顶级评论）
            load_user: 是否加载用户信息
            
        Returns:
            List[Comment]: 评论列表
        """
        conditions = [Comment.video_id == video_id]
        
        if parent_id is not None:
            # 获取指定父评论的回复
            conditions.append(Comment.parent_id == parent_id)
        else:
            # 获取顶级评论（parent_id为NULL）
            conditions.append(Comment.parent_id.is_(None))
        
        query = select(Comment).where(
            and_(*conditions)
        ).order_by(Comment.created_at.desc()).offset(skip).limit(limit)
        
        if load_user:
            query = query.options(joinedload(Comment.user))
        
        result = await db.execute(query)
        return list(result.scalars().unique().all())
    
    async def get_by_user(
        self, 
        db: AsyncSession, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20,
        load_video: bool = True
    ) -> List[Comment]:
        """
        获取用户的评论列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过数量
            limit: 返回数量限制
            load_video: 是否加载视频信息
            
        Returns:
            List[Comment]: 评论列表
        """
        query = select(Comment).where(Comment.user_id == user_id).order_by(
            Comment.created_at.desc()
        ).offset(skip).limit(limit)
        
        if load_video:
            query = query.options(joinedload(Comment.video))
        
        result = await db.execute(query)
        return list(result.scalars().unique().all())
    
    async def get_replies(
        self, 
        db: AsyncSession, 
        comment_id: int, 
        skip: int = 0, 
        limit: int = 20,
        load_user: bool = True
    ) -> List[Comment]:
        """
        获取评论的回复列表
        
        Args:
            db: 数据库会话
            comment_id: 父评论ID
            skip: 跳过数量
            limit: 返回数量限制
            load_user: 是否加载用户信息
            
        Returns:
            List[Comment]: 回复列表
        """
        query = select(Comment).where(Comment.parent_id == comment_id).order_by(
            Comment.created_at.asc()
        ).offset(skip).limit(limit)
        
        if load_user:
            query = query.options(joinedload(Comment.user))
        
        result = await db.execute(query)
        return list(result.scalars().unique().all())
    
    async def count_by_video(
        self, 
        db: AsyncSession, 
        video_id: int,
        parent_id: Optional[int] = None
    ) -> int:
        """
        统计视频的评论总数
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            parent_id: 父评论ID（None表示统计所有评论）
            
        Returns:
            int: 评论总数
        """
        conditions = [Comment.video_id == video_id]
        
        if parent_id is not None:
            conditions.append(Comment.parent_id == parent_id)
        
        query = select(func.count(Comment.id)).where(and_(*conditions))
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def count_by_user(self, db: AsyncSession, user_id: int) -> int:
        """
        统计用户的评论总数
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            int: 评论总数
        """
        query = select(func.count(Comment.id)).where(Comment.user_id == user_id)
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def count_replies(
        self, 
        db: AsyncSession, 
        comment_id: int
    ) -> int:
        """
        统计评论的回复数量
        
        Args:
            db: 数据库会话
            comment_id: 父评论ID
            
        Returns:
            int: 回复数量
        """
        query = select(func.count(Comment.id)).where(Comment.parent_id == comment_id)
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def increment_like_count(
        self, 
        db: AsyncSession, 
        comment_id: int
    ) -> bool:
        """
        增加评论点赞数
        
        Args:
            db: 数据库会话
            comment_id: 评论ID
            
        Returns:
            bool: 是否成功
        """
        query = update(Comment).where(
            Comment.id == comment_id
        ).values(like_count=Comment.like_count + 1)
        result = await db.execute(query)
        return result.rowcount > 0
    
    async def decrement_like_count(
        self, 
        db: AsyncSession, 
        comment_id: int
    ) -> bool:
        """
        减少评论点赞数
        
        Args:
            db: 数据库会话
            comment_id: 评论ID
            
        Returns:
            bool: 是否成功
        """
        query = update(Comment).where(
            and_(Comment.id == comment_id, Comment.like_count > 0)
        ).values(like_count=Comment.like_count - 1)
        result = await db.execute(query)
        return result.rowcount > 0
    
    async def get_comments_tree(
        self,
        db: AsyncSession,
        video_id: int,
        skip: int = 0,
        limit: int = 20,
        load_user: bool = True
    ) -> List[Comment]:
        """
        获取视频评论树形结构（包含顶级评论及其直接回复）
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            skip: 跳过数量
            limit: 返回数量限制（针对顶级评论）
            load_user: 是否加载用户信息
            
        Returns:
            List[Comment]: 顶级评论列表（每条评论包含其replies属性）
        """
        # 获取顶级评论
        top_level_comments = await self.get_by_video(
            db, video_id, skip, limit, parent_id=None, load_user=load_user
        )
        
        # 为每条顶级评论加载回复（最多加载3条直接回复）
        for comment in top_level_comments:
            if load_user:
                # 重新加载评论以获取replies关系
                comment_with_replies = await self.get_by_id(
                    db, comment.id, load_user=load_user, load_replies=True
                )
                if comment_with_replies:
                    comment.replies = comment_with_replies.replies[:3]
            else:
                replies = await self.get_replies(db, comment.id, 0, 3, load_user=False)
                comment.replies = replies
        
        return top_level_comments


# 创建全局 CRUD 实例
comment_crud = CommentCRUD()
