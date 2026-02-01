from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.models.user import User
from app.core.exception import UnauthorizedException, ForbiddenException
from app.core.config import settings
from app.crud import user_crud



from app.utils.security import (
    decode_access_token,
    verify_token,
    get_user_id_from_token
)





# OAuth2 密码流，tokenUrl 指向 OAuth2 token 端点
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/token")


async def get_db() -> AsyncSession:
    """
    数据库会话依赖注入
    用于 FastAPI 的依赖注入系统
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前用户
    从请求头中解析 token，验证并返回用户对象
    
    Args:
        token: OAuth2 token（从请求头自动提取）
        db: 数据库会话
        
    Returns:
        User: 当前用户对象
        
    Raises:
        UnauthorizedException: token 无效或用户不存在
    """
    
    


    # 从token中获取用户ID
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise UnauthorizedException("无效的 token，请先登录")



    
    # 查询用户
    user = await user_crud.get_by_id(db, user_id)
    if not user:
        raise UnauthorizedException("用户不存在或已被删除")
    
    # 检查用户是否被删除
    if user.isDelete != 0:
        raise UnauthorizedException("用户已被删除")
    
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    要求管理员权限
    只有 admin 角色才能访问
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        User: 当前用户对象（确保是 admin）
        
    Raises:
        ForbiddenException: 非管理员用户
    """
    if current_user.userRole != "admin":
        raise ForbiddenException("需要管理员权限")
    return current_user


def check_owner_or_admin(user_id: int, current_user: User) -> None:
    """
    检查是否是本人或管理员
    用于修改自己信息或管理员操作他人信息的场景
    
    Args:
        user_id: 要操作的用户ID
        current_user: 当前用户对象
        
    Raises:
        ForbiddenException: 既不是本人也不是管理员
    """
    if current_user.id != user_id and current_user.userRole != "admin":
        raise ForbiddenException("只能修改自己的信息或需要管理员权限")