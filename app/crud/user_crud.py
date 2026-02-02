from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.user import User
from typing import Optional, List, Tuple


class UserCRUD:
    """
    用户CRUD操作类
    """
    
    async def get_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """
        根据ID获取用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            Optional[User]: 用户对象，如果不存在返回None
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            db: 数据库会话
            username: 用户名
            
        Returns:
            Optional[User]: 用户对象，如果不存在返回None
        """
        result = await db.execute(select(User).where(User.user_name == username))
        return result.scalar_one_or_none()
    
    async def create(self, db: AsyncSession, user_data: dict) -> User:
        """
        创建用户
        
        Args:
            db: 数据库会话
            user_data: 用户数据
            
        Returns:
            User: 创建的用户对象
        """
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    async def update(self, db: AsyncSession, user_id: int, update_data: dict) -> Optional[User]:
        """
        更新用户信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            update_data: 更新的数据
            
        Returns:
            Optional[User]: 更新后的用户对象，如果用户不存在返回None
        """
        user = await self.get_by_id(db, user_id)
        if not user:
            return None
        
        for key, value in update_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        await db.commit()
        await db.refresh(user)
        return user
    
    async def delete(self, db: AsyncSession, user_id: int) -> bool:
        """
        删除用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            bool: 删除是否成功
        """
        user = await self.get_by_id(db, user_id)
        if not user:
            return False
        
        await db.delete(user)
        await db.commit()
        return True
    
    async def list_users(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """
        获取用户列表
        
        Args:
            db: 数据库会话
            skip: 跳过条数
            limit: 限制条数
            
        Returns:
            List[User]: 用户列表
        """
        result = await db.execute(
            select(User)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_users_with_filters(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        username: Optional[str] = None,
        user_role: Optional[str] = None
    ) -> List[User]:
        """
        根据条件获取用户列表
        
        Args:
            db: 数据库会话
            skip: 跳过条数
            limit: 限制条数
            username: 用户名筛选（模糊匹配）
            user_role: 用户角色筛选
            
        Returns:
            List[User]: 用户列表
        """
        query = select(User)
        
        # 添加筛选条件
        if username:
            query = query.where(User.user_name.ilike(f"%{username}%"))
        
        if user_role:
            query = query.where(User.userRole == user_role)
        
        result = await db.execute(
            query.offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def count_users_with_filters(
        self,
        db: AsyncSession,
        username: Optional[str] = None,
        user_role: Optional[str] = None
    ) -> int:
        """
        根据条件统计用户数量
        
        Args:
            db: 数据库会话
            username: 用户名筛选（模糊匹配）
            user_role: 用户角色筛选
            
        Returns:
            int: 用户数量
        """
        from sqlalchemy import func
        
        query = select(func.count()).select_from(User)
        
        # 添加筛选条件
        if username:
            query = query.where(User.user_name.ilike(f"%{username}%"))
        
        if user_role:
            query = query.where(User.userRole == user_role)
        
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def get_multiple_users(
        self,
        db: AsyncSession,
        user_ids: List[int]
    ) -> List[User]:
        """
        批量获取用户信息
        
        Args:
            db: 数据库会话
            user_ids: 用户ID列表
            
        Returns:
            List[User]: 用户列表
        """
        if not user_ids:
            return []
        
        query = select(User).where(User.id.in_(user_ids))
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def increment_follow_count(self, db: AsyncSession, user_id: int) -> bool:
        """
        增加用户的关注数（业务逻辑中维护）
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            bool: 是否成功
        """
        from sqlalchemy import update
        query = update(User).where(User.id == user_id).values(
            follow_count=User.follow_count + 1
        )
        result = await db.execute(query)
        return result.rowcount > 0
    
    async def decrement_follow_count(self, db: AsyncSession, user_id: int) -> bool:
        """
        减少用户的关注数（业务逻辑中维护）
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            bool: 是否成功
        """
        from sqlalchemy import update
        query = update(User).where(
            and_(User.id == user_id, User.follow_count > 0)
        ).values(follow_count=User.follow_count - 1)
        result = await db.execute(query)
        return result.rowcount > 0
    
    async def increment_follower_count(self, db: AsyncSession, user_id: int) -> bool:
        """
        增加用户的粉丝数（业务逻辑中维护）
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            bool: 是否成功
        """
        from sqlalchemy import update
        query = update(User).where(User.id == user_id).values(
            follower_count=User.follower_count + 1
        )
        result = await db.execute(query)
        return result.rowcount > 0
    
    async def decrement_follower_count(self, db: AsyncSession, user_id: int) -> bool:
        """
        减少用户的粉丝数（业务逻辑中维护）
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            bool: 是否成功
        """
        from sqlalchemy import update
        query = update(User).where(
            and_(User.id == user_id, User.follower_count > 0)
        ).values(follower_count=User.follower_count - 1)
        result = await db.execute(query)
        return result.rowcount > 0


# 创建全局CRUD实例
user_crud = UserCRUD()