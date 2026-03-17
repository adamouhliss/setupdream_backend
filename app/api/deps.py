from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import SessionLocal
from ..core.security import ALGORITHM
from ..models.user import User
from ..schemas.user import TokenPayload

reusable_oauth2 = HTTPBearer()
optional_oauth2 = HTTPBearer(auto_error=False)


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), token: HTTPAuthorizationCredentials = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token.credentials, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


def get_current_user_or_none(
    db: Session = Depends(get_db), 
    token: Optional[HTTPAuthorizationCredentials] = Depends(optional_oauth2)
) -> Optional[User]:
    """Get current user or None if not authenticated"""
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token.credentials, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        user = db.query(User).filter(User.id == token_data.sub).first()
        return user if user and user.is_active else None
    except (jwt.JWTError, ValidationError):
        return None 