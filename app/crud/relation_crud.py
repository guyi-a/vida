"""
用户关系 CRUD 操作
提供关注、取消关注、查询关注列表和粉丝列表等功能
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete, update
from typing import Optional, List, Dict, Any
from app.models.relation import Relation
from app.models.user import User


class RelationCRUD:
    """
    用户关系 CRUD 操作类
    """
    
    async def create(
        self, 
        db: AsyncSession, 
        follower_id: int, 
        follow_id: int
    ) -> Relation:
        """
        创建关注关系
        
        Args:
            db: 数据库会话
            follower_id: 粉丝用户ID（关注者）
            follow_id: 被关注的用户ID（被关注者）
            
        Returns:
            Relation: 创建的关系对象
            
        Raises:
            Exception: 如果关系已存在会抛出数据库异常
        """
        relation = Relation(
            follower_id=follower_id,
            follow_id=follow_id
        )
        db.add(relation)
        await db.flush()
        await db.refresh(relation)
        
        # 更新关注者（当前用户）的关注数
        from app.crud import user_crud
        await user_crud.increment_follow_count(db, follower_id)
        
        # 更新被关注者的粉丝数
        await user_crud.increment_follower_count(db, follow_id)
        
        return relation
    
    async def delete(
        self, 
        db: AsyncSession, 
        follower_id: int, 
        follow_id: int
    ) -> bool:
        """
        删除关注关系（取消关注）
        
        Args:
            db: 数据库会话
            follower_id: 粉丝用户ID（关注者）
            follow_id: 被关注的用户ID（被关注者）
            
        Returns:
            bool: 是否删除成功
        """
        query = delete(Relation).where(
            and_(Relation.follower_id == follower_id, Relation.follow_id == follow_id)
        )
        result = await db.execute(query)
        
        if result.rowcount > 0:
            # 更新关注者（当前用户）的关注数
            from app.crud import user_crud
            await user_crud.decrement_follow_count(db, follower_id)
            
            # 更新被关注者的粉丝数
            await user_crud.decrement_follower_count(db, follow_id)
            
            return True
        
        return False
    
    async def get_relation(
        self, 
        db: AsyncSession, 
        follower_id: int, 
        follow_id: int
    ) -> Optional[Relation]:
        """
        获取关注关系
        
        Args:
            db: 数据库会话
            follower_id: 粉丝用户ID（关注者）
            follow_id: 被关注的用户ID（被关注者）
            
        Returns:
            Optional[Relation]: 关系对象，如果不存在返回None
        """
        query = select(Relation).where(
            and_(Relation.follower_id == follower_id, Relation.follow_id == follow_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def is_following(
        self, 
        db: AsyncSession, 
        follower_id: int, 
        follow_id: int
    ) -> bool:
        """
        检查是否已关注
        
        Args:
            db: 数据库会话
            follower_id: 粉丝用户ID（关注者）
            follow_id: 被关注的用户ID（被关注者）
            
        Returns:
            bool: 是否已关注
        """
        relation = await self.get_relation(db, follower_id, follow_id)
        return relation is not None
    
    async def get_following_list(
        self, 
        db: AsyncSession, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Relation]:
        """
        获取用户的关注列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            List[Relation]: 关注关系列表
        """
        query = select(Relation).where(Relation.follower_id == user_id).order_by(
            Relation.created_at.desc()
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_follower_list(
        self, 
        db: AsyncSession, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Relation]:
        """
        获取用户的粉丝列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            List[Relation]: 粉丝关系列表
        """
        query = select(Relation).where(Relation.follow_id == user_id).order_by(
            Relation.created_at.desc()
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def count_following(self, db: AsyncSession, user_id: int) -> int:
        """
        统计用户的关注数
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            int: 关注数
        """
        query = select(func.count(Relation.id)).where(Relation.follower_id == user_id)
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def count_followers(self, db: AsyncSession, user_id: int) -> int:
        """
        统计用户的粉丝数
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            int: 粉丝数
        """
        query = select(func.count(Relation.id)).where(Relation.follow_id == user_id)
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def get_multiple_users_following_status(
        self,
        db: AsyncSession,
        follower_id: int,
        follow_ids: List[int]
    ) -> Dict[int, bool]:
        """
        批量获取用户对多个其他用户的关注状态
        
        Args:
            db: 数据库会话
            follower_id: 当前用户ID
            follow_ids: 目标用户ID列表
            
        Returns:
            Dict[int, bool]: 用户ID到关注状态的映射
        """
        if not follow_ids:
            return {}
        
        query = select(Relation.follow_id).where(
            and_(
                Relation.follower_id == follower_id,
                Relation.follow_id.in_(follow_ids)
            )
        )
        result = await db.execute(query)
        followed_user_ids = set(result.scalars().all())
        
        return {user_id: user_id in followed_user_ids for user_id in follow_ids}
    
    async def get_mutual_followers(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取互相关注的用户列表（双向关注）
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 互相关注的用户信息列表
        """
        # 查询互相关注的用户：
        # 1. user_id 关注了 target_id
        # 2. target_id 也关注了 user_id
        subquery_following = (
            select(Relation.follow_id)
            .where(Relation.follower_id == user_id)
        )
        
        subquery_followers = (
            select(Relation.follower_id)
            .where(Relation.follow_id == user_id)
        )
        
        # 使用子查询获取互相关注的用户ID
        from sqlalchemy import intersect
        mutual_user_ids_query = intersect(subquery_following, subquery_followers)
        
        result = await db.execute(mutual_user_ids_query.limit(limit).offset(skip))
        mutual_user_ids = result.scalars().all()
        
        # 构建互相关注的关系信息
        mutual_relations = []
        for target_id in mutual_user_ids:
            mutual_relations.append({
                "user_id": target_id,
                "relation_type": "mutual"  # 互相关注
            })
        
        return mutual_relations
    
    async def count_mutual_followers(self, db: AsyncSession, user_id: int) -> int:
        """
        统计互相关注的用户数量
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            int: 互相关注数量
        """
        subquery_following = (
            select(Relation.follow_id)
            .where(Relation.follower_id == user_id)
        )
        
        subquery_followers = (
            select(Relation.follower_id)
            .where(Relation.follow_id == user_id)
        )
        
        from sqlalchemy import intersect, func
        mutual_count_query = select(func.count()).select_from(
            intersect(subquery_following, subquery_followers)
        )
        
        result = await db.execute(mutual_count_query)
        return result.scalar() or 0


# 创建全局 CRUD 实例
relation_crud = RelationCRUD()
