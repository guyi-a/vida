from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext


# 延迟导入配置，避免循环依赖
_settings = None


def get_settings():
    """获取配置，延迟加载避免循环导入"""
    global _settings
    if _settings is None:
        from app.core.config import settings as config_settings
        _settings = config_settings
    return _settings


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== 密码哈希相关函数 ====================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)


# ==================== JWT 相关函数 ====================


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        data: 要编码到 token 中的数据（通常是用户ID、用户名等）
        expires_delta: 过期时间增量，如果为 None 则使用配置中的默认值
        
    Returns:
        str: JWT token
    """
    settings = get_settings()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码访问令牌
    
    Args:
        token: JWT token
        
    Returns:
        Optional[Dict[str, Any]]: 解码后的数据，如果 token 无效则返回 None
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> bool:
    """
    验证 token 是否有效
    
    Args:
        token: JWT token
        
    Returns:
        bool: token 是否有效
    """
    payload = decode_access_token(token)
    return payload is not None


def get_user_id_from_token(token: str) -> Optional[int]:
    """
    从 token 中获取用户ID
    
    Args:
        token: JWT token
        
    Returns:
        Optional[int]: 用户ID，如果 token 无效则返回 None
    """
    payload = decode_access_token(token)
    if payload:
        user_id = payload.get("sub")
        if user_id:
            try:
                return int(user_id)
            except (ValueError, TypeError):
                return None
    return None


def get_username_from_token(token: str) -> Optional[str]:
    """
    从 token 中获取用户名
    
    Args:
        token: JWT token
        
    Returns:
        Optional[str]: 用户名，如果 token 无效则返回 None
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("username")
    return None