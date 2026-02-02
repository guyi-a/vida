from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.orm import joinedload
from app.models.video import Video
from typing import Optional, List, Dict, Any


class VideoCRUD:
    """
    视频 CRUD 操作类
    """
    
    async def get_by_id(self, db: AsyncSession, video_id: int, load_author: bool = False) -> Optional[Video]:
        """
        根据ID获取视频
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            load_author: 是否加载作者信息
            
        Returns:
            Optional[Video]: 视频对象，如果不存在返回None
        """
        query = select(Video).where(Video.id == video_id)
        if load_author:
            query = query.options(joinedload(Video.author))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_id_and_author(self, db: AsyncSession, video_id: int, author_id: int) -> Optional[Video]:
        """
        根据ID和作者ID获取视频（用于权限检查）
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            author_id: 作者ID
            
        Returns:
            Optional[Video]: 视频对象，如果不存在或不属于该作者返回None
        """
        query = select(Video).where(
            and_(Video.id == video_id, Video.author_id == author_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, db: AsyncSession, video_data: Dict[str, Any]) -> Video:
        """
        创建视频
        
        Args:
            db: 数据库会话
            video_data: 视频数据
            
        Returns:
            Video: 创建的视频对象
        """
        video = Video(**video_data)
        db.add(video)
        await db.commit()
        await db.refresh(video)
        return video
    
    async def update(self, db: AsyncSession, video_id: int, update_data: Dict[str, Any]) -> Optional[Video]:
        """
        更新视频信息
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            update_data: 更新的数据
            
        Returns:
            Optional[Video]: 更新后的视频对象，如果视频不存在返回None
        """
        video = await self.get_by_id(db, video_id)
        if not video:
            return None
        
        # 更新字段
        for key, value in update_data.items():
            if hasattr(video, key) and value is not None:
                setattr(video, key, value)
        
        await db.commit()
        await db.refresh(video)
        return video
    
    async def delete(self, db: AsyncSession, video_id: int) -> bool:
        """
        删除视频（软删除）
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            
        Returns:
            bool: 删除是否成功
        """
        video = await self.get_by_id(db, video_id)
        if not video:
            return False
        
        # 软删除：更新状态为deleted
        video.status = "deleted"
        await db.commit()
        return True
    
    async def list_videos(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        author_id: Optional[int] = None,
        search: Optional[str] = None,
        load_author: bool = False
    ) -> List[Video]:
        """
        获取视频列表
        
        Args:
            db: 数据库会话
            skip: 跳过条数
            limit: 限制条数
            status: 状态筛选
            author_id: 作者ID筛选
            search: 搜索关键词（标题或描述）
            load_author: 是否加载作者信息
            
        Returns:
            List[Video]: 视频列表
        """
        query = select(Video)
        
        # 如果需要加载作者信息，使用 joinedload
        if load_author:
            query = query.options(joinedload(Video.author))
        
        # 构建筛选条件
        conditions = []
        
        if status:
            conditions.append(Video.status == status)
            # 如果查询已发布的视频，确保 play_url 不为空（视频已转码并上传到公有桶）
            if status == "published":
                conditions.append(Video.play_url.isnot(None))
        
        if author_id:
            conditions.append(Video.author_id == author_id)
        
        if search:
            conditions.append(
                or_(
                    Video.title.ilike(f"%{search}%"),
                    Video.description.ilike(f"%{search}%"),
                )
            )
        
        # 添加筛选条件
        if conditions:
            query = query.where(and_(*conditions))
        
        # 按创建时间倒序
        query = query.order_by(Video.created_at.desc())
        
        result = await db.execute(
            query.offset(skip).limit(limit)
        )
        return result.scalars().unique().all()
    
    async def count_videos(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        author_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> int:
        """
        统计视频数量
        
        Args:
            db: 数据库会话
            status: 状态筛选
            author_id: 作者ID筛选
            search: 搜索关键词
            
        Returns:
            int: 视频数量
        """
        query = select(func.count()).select_from(Video)
        
        # 构建筛选条件
        conditions = []
        
        if status:
            conditions.append(Video.status == status)
            # 如果查询已发布的视频，确保 play_url 不为空（视频已转码并上传到公有桶）
            if status == "published":
                conditions.append(Video.play_url.isnot(None))
        
        if author_id:
            conditions.append(Video.author_id == author_id)
        
        if search:
            conditions.append(
                or_(
                    Video.title.ilike(f"%{search}%"),
                    Video.description.ilike(f"%{search}%"),
                )
            )
        
        # 添加筛选条件
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def increment_view_count(self, db: AsyncSession, video_id: int) -> bool:
        """
        增加视频观看次数（使用数据库原子操作）
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            
        Returns:
            bool: 更新是否成功
        """
        stmt = (
            update(Video)
            .where(Video.id == video_id)
            .values(view_count=Video.view_count + 1)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
    
    async def increment_comment_count(self, db: AsyncSession, video_id: int) -> bool:
        """
        增加视频评论数（使用数据库原子操作）
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            
        Returns:
            bool: 更新是否成功
        """
        stmt = (
            update(Video)
            .where(Video.id == video_id)
            .values(comment_count=Video.comment_count + 1)
        )
        result = await db.execute(stmt)
        return result.rowcount > 0
    
    async def decrement_comment_count(self, db: AsyncSession, video_id: int) -> bool:
        """
        减少视频评论数（使用数据库原子操作）
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            
        Returns:
            bool: 更新是否成功
        """
        stmt = (
            update(Video)
            .where(and_(Video.id == video_id, Video.comment_count > 0))
            .values(comment_count=Video.comment_count - 1)
        )
        result = await db.execute(stmt)
        return result.rowcount > 0
    
    async def increment_favorite_count(self, db: AsyncSession, video_id: int) -> bool:
        """
        增加视频点赞数（使用数据库原子操作）
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            
        Returns:
            bool: 更新是否成功
        """
        stmt = (
            update(Video)
            .where(Video.id == video_id)
            .values(favorite_count=Video.favorite_count + 1)
        )
        result = await db.execute(stmt)
        return result.rowcount > 0
    
    async def decrement_favorite_count(self, db: AsyncSession, video_id: int) -> bool:
        """
        减少视频点赞数（使用数据库原子操作）
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            
        Returns:
            bool: 更新是否成功
        """
        stmt = (
            update(Video)
            .where(and_(Video.id == video_id, Video.favorite_count > 0))
            .values(favorite_count=Video.favorite_count - 1)
        )
        result = await db.execute(stmt)
        return result.rowcount > 0


# 创建全局CRUD实例
video_crud = VideoCRUD()
