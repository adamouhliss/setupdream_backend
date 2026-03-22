from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, EmailStr, validator
from pydantic_settings import BaseSettings
from decouple import config


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = config("SECRET_KEY", default="setupdream-super-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database - PostgreSQL (Railway)
    DATABASE_URL: str = config("DATABASE_URL", default="postgresql://postgres:LwvemmnYzpTiNrJTCateqWzZfDaYDbue@yamabiko.proxy.rlwy.net:48809/railway").replace("postgres://", "postgresql://", 1)

    
    # CORS
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = config("BACKEND_CORS_ORIGINS", default="http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:8080,https://projects-second.mlqyyh.easypanel.host,https://projects-backend.mlqyyh.easypanel.host")

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str = "Setup dreams API"
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # Stripe
    STRIPE_SECRET_KEY: str = config("STRIPE_SECRET_KEY", default="sk_test_...")
    STRIPE_PUBLISHABLE_KEY: str = config("STRIPE_PUBLISHABLE_KEY", default="pk_test_...")
    
    # File upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB

    # Admin user
    FIRST_SUPERUSER: EmailStr = "admin@setupdream.com"
    FIRST_SUPERUSER_PASSWORD: str = "setupdream@2024!Admin#Secure789"

    class Config:
        case_sensitive = True


settings = Settings() 