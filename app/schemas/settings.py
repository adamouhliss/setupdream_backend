from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr


class StoreSettings(BaseModel):
    store_name: str = "Carré Sports"
    store_description: str = "Carrément sport"
    store_logo_url: Optional[str] = None
    store_favicon_url: Optional[str] = None
    store_address: str = "Casablanca, Morocco"
    store_phone: str = "+212 5XX-XXXXXX"
    store_email: EmailStr = "info@carresports.ma"
    currency: str = "MAD"
    timezone: str = "Africa/Casablanca"
    language: str = "fr"
    tax_rate: float = 20.0
    shipping_cost: float = 50.0
    free_shipping_threshold: float = 500.0
    
    # Social Media URLs
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    youtube_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    linkedin_url: Optional[str] = None


class SecuritySettings(BaseModel):
    session_timeout: int = 3600
    max_login_attempts: int = 5
    require_email_verification: bool = True
    enable_two_factor: bool = False
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_symbols: bool = False


class EmailSettings(BaseModel):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    from_email: EmailStr = "noreply@carresports.ma"
    from_name: str = "Carré Sports"
    enable_order_notifications: bool = True
    enable_low_stock_alerts: bool = True
    enable_welcome_emails: bool = True
    enable_marketing_emails: bool = False


class NotificationSettings(BaseModel):
    enable_browser_notifications: bool = True
    enable_email_alerts: bool = True
    enable_sms_alerts: bool = False
    low_stock_threshold_global: int = 10
    order_notification_roles: List[str] = ["admin", "manager"]
    maintenance_mode: bool = False
    debug_mode: bool = False


class SettingsBase(BaseModel):
    category: str
    key: str
    value: Optional[str] = None
    data_type: str = "string"


class SettingsCreate(SettingsBase):
    pass


class SettingsUpdate(BaseModel):
    value: Optional[str] = None
    data_type: Optional[str] = None


class SettingsResponse(SettingsBase):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]


class SettingsEmailTest(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool
    from_email: EmailStr
    from_name: str 