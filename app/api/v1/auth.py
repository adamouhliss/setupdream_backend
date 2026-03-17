from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...api.deps import get_current_active_user, get_db
from ...core.config import settings
from ...core.security import create_access_token
from ...crud.user import user
from ...models.user import User
from ...schemas.user import Token, User as UserSchema, UserCreate, UserLogin, UserResponse

router = APIRouter()


@router.post("/login", response_model=Token)
def login_access_token(
    *,
    db: Session = Depends(get_db), 
    form_data: UserLogin
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user_obj = user.authenticate(
        db, email=form_data.email, password=form_data.password
    )
    if not user_obj:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active(user_obj):
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user_obj.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/register", response_model=UserResponse)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user.
    """
    user_obj = user.get_by_email(db, email=user_in.email)
    if user_obj:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user_obj = user.create(db, obj_in=user_in)
    return user_obj


@router.post("/test-token", response_model=UserResponse)
def test_token(current_user: User = Depends(get_current_active_user)) -> Any:
    """
    Test access token
    """
    return current_user


@router.get("/me", response_model=UserResponse)
def read_user_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user 