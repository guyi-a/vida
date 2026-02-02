"""
点赞 CRUD 操作
提供用户点赞视频、取消点赞、查询点赞状态等功能
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from typing import Optional, List, Dict
from app.models.favorite import Favorite
from app.models.video import Video


class FavoriteCRUD:
    """
    点赞 CRUD 操作类
    """
    
    async def create(self, db: AsyncSession, user_id: int, video_id: int) -> Favorite:
        """
        创建点赞记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            video_id: 视频ID
            
        Returns:
            Favorite: 创建的点赞对象
            
        Raises:
            Exception: 如果点赞记录已存在会抛出数据库异常
        """
        favorite = Favorite(
            user_id=user_id,
            video_id=video_id
        )
        db.add(favorite)
        await db.flush()
        await db.refresh(favorite)
        return favorite
    
    async def delete(self, db: AsyncSession, user_id: int, video_id: int) -> bool:
        """
        删除点赞记录（取消点赞）
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            video_id: 视频ID
            
        Returns:
            bool: 是否删除成功
        """
        query = delete(Favorite).where(
            and_(Favorite.user_id == user_id, Favorite.video_id == video_id)
        )
        result = await db.execute(query)
        return result.rowcount > 0
    
    async def get_by_user_and_video(
        self, 
        db: AsyncSession, 
        user_id: int, 
        video_id: int
    ) -> Optional[Favorite]:
        """
        获取用户对视频的点赞记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            video_id: 视频ID
            
        Returns:
            Optional[Favorite]: 点赞对象，如果不存在返回None
        """
        query = select(Favorite).where(
            and_(Favorite.user_id == user_id, Favorite.video_id == video_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_user(
        self, 
        db: AsyncSession, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Favorite]:
        """
        获取用户的点赞列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            List[Favorite]: 点赞记录列表
        """
        query = select(Favorite).where(Favorite.user_id == user_id).order_by(
            Favorite.created_at.desc()
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_video(
        self, 
        db: AsyncSession, 
        video_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Favorite]:
        """
        获取视频的点赞记录列表
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            List[Favorite]: 点赞记录列表
        """
        query = select(Favorite).where(Favorite.video_id == video_id).order_by(
            Favorite.created_at.desc()
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def count_by_user(self, db: AsyncSession, user_id: int) -> int:
        """
        统计用户的点赞总数
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            int: 点赞总数
        """
        query = select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def count_by_video(self, db: AsyncSession, video_id: int) -> int:
        """
        统计视频的点赞总数
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            
        Returns:
            int: 点赞总数
        """
        query = select(func.count(Favorite.id)).where(Favorite.video_id == video_id)
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def is_favorited(
        self, 
        db: AsyncSession, 
        user_id: int, 
        video_id: int
    ) -> bool:
        """
        检查用户是否已点赞该视频
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            video_id: 视频ID
            
        Returns:
            bool: 是否已点赞
        """
        favorite = await self.get_by_user_and_video(db, user_id, video_id)
        return favorite is not None
    
    async def get_multiple_videos_favorited_status(
        self,
        db: AsyncSession,
        user_id: int,
        video_ids: List[int]
    ) -> Dict[int, bool]:
        """
        批量获取用户对多个视频的点赞状态
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            video_ids: 视频ID列表
            
        Returns:
            Dict[int, bool]: 视频ID到点赞状态的映射
        """
        if not video_ids:
            return {}
        
        query = select(Favorite.video_id).where(
            and_(Favorite.user_id == user_id, Favorite.video_id.in_(video_ids))
        )
        result = await db.execute(query)
        favorited_video_ids = set(result.scalars().all())
        
        return {video_id: video_id in favorited_video_ids for video_id in video_ids}
    
    async def get_favorited_video_ids(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[int]:
        """
        获取用户点赞的视频ID列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            List[int]: 视频ID列表
        """
        query = select(Favorite.video_id).where(Favorite.user_id == user_id).order_by(
            Favorite.created_at.desc()
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


# 创建全局 CRUD 实例
favorite_crud = FavoriteCRUD()
