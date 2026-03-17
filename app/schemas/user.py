from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_active: bool = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False
    has_used_first_time_discount: Optional[bool] = False
    is_influencer: Optional[bool] = False
    promo_code: Optional[str] = None
    commission_rate: Optional[float] = 10.0
    customer_discount_rate: Optional[float] = 10.0


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None
    has_used_first_time_discount: Optional[bool] = None
    is_influencer: Optional[bool] = None
    promo_code: Optional[str] = None
    commission_rate: Optional[float] = None
    customer_discount_rate: Optional[float] = None


class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str


class UserResponse(UserInDBBase):
    pass


# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[int] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str 