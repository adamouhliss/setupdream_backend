from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from ...api.deps import get_current_active_superuser, get_db
from ...crud.settings import settings
from ...models.user import User
from ...services.image_service import ImageService
from ...schemas.settings import (
    StoreSettings, SecuritySettings, EmailSettings, NotificationSettings,
    SettingsUpdateRequest, SettingsEmailTest
)

router = APIRouter()


@router.get("/store/public")
def get_public_store_settings(
    db: Session = Depends(get_db),
) -> StoreSettings:
    """
    Get public store settings (no authentication required).
    This endpoint is used by the frontend to display store information.
    """
    settings_dict = settings.get_category_as_dict(db, category="store")
    
    # Merge with defaults
    store_defaults = StoreSettings()
    for key, value in settings_dict.items():
        if hasattr(store_defaults, key):
            setattr(store_defaults, key, value)
    
    return store_defaults


@router.get("/store")
def get_store_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> StoreSettings:
    """
    Get store settings (admin only).
    """
    settings_dict = settings.get_category_as_dict(db, category="store")
    
    # Merge with defaults
    store_defaults = StoreSettings()
    for key, value in settings_dict.items():
        if hasattr(store_defaults, key):
            setattr(store_defaults, key, value)
    
    return store_defaults


@router.put("/store")
def update_store_settings(
    *,
    db: Session = Depends(get_db),
    settings_in: StoreSettings,
    current_user: User = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Update store settings (admin only).
    """
    settings_dict = settings_in.dict()
    settings.bulk_upsert_category(db, category="store", settings_dict=settings_dict)
    
    return {"message": "Store settings updated successfully", "settings": settings_dict}


@router.get("/security")
def get_security_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> SecuritySettings:
    """
    Get security settings (admin only).
    """
    settings_dict = settings.get_category_as_dict(db, category="security")
    
    # Merge with defaults
    security_defaults = SecuritySettings()
    for key, value in settings_dict.items():
        if hasattr(security_defaults, key):
            setattr(security_defaults, key, value)
    
    return security_defaults


@router.put("/security")
def update_security_settings(
    *,
    db: Session = Depends(get_db),
    settings_in: SecuritySettings,
    current_user: User = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Update security settings (admin only).
    """
    settings_dict = settings_in.dict()
    settings.bulk_upsert_category(db, category="security", settings_dict=settings_dict)
    
    return {"message": "Security settings updated successfully", "settings": settings_dict}


@router.get("/email")
def get_email_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> EmailSettings:
    """
    Get email settings (admin only).
    """
    settings_dict = settings.get_category_as_dict(db, category="email")
    
    # Merge with defaults
    email_defaults = EmailSettings()
    for key, value in settings_dict.items():
        if hasattr(email_defaults, key):
            setattr(email_defaults, key, value)
    
    return email_defaults


@router.put("/email")
def update_email_settings(
    *,
    db: Session = Depends(get_db),
    settings_in: EmailSettings,
    current_user: User = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Update email settings (admin only).
    """
    settings_dict = settings_in.dict()
    settings.bulk_upsert_category(db, category="email", settings_dict=settings_dict)
    
    return {"message": "Email settings updated successfully", "settings": settings_dict}


@router.get("/notifications")
def get_notification_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> NotificationSettings:
    """
    Get notification settings (admin only).
    """
    settings_dict = settings.get_category_as_dict(db, category="notifications")
    
    # Merge with defaults
    notification_defaults = NotificationSettings()
    for key, value in settings_dict.items():
        if hasattr(notification_defaults, key):
            setattr(notification_defaults, key, value)
    
    return notification_defaults


@router.put("/notifications")
def update_notification_settings(
    *,
    db: Session = Depends(get_db),
    settings_in: NotificationSettings,
    current_user: User = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Update notification settings (admin only).
    """
    settings_dict = settings_in.dict()
    settings.bulk_upsert_category(db, category="notifications", settings_dict=settings_dict)
    
    return {"message": "Notification settings updated successfully", "settings": settings_dict}


@router.post("/test-email")
def test_email_connection(
    *,
    db: Session = Depends(get_db),
    email_config: SettingsEmailTest,
    current_user: User = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Test email configuration by sending a test email (admin only).
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{email_config.from_name} <{email_config.from_email}>"
        msg['To'] = current_user.email
        msg['Subject'] = "Carré Sports - Email Configuration Test"
        
        body = f"""
        <html>
        <body>
            <h2>Email Configuration Test</h2>
            <p>Hello {current_user.first_name or 'Admin'},</p>
            <p>This is a test email to verify your email configuration is working correctly.</p>
            <p>If you receive this email, your SMTP settings are configured properly.</p>
            <br>
            <p>Best regards,<br>Carré Sports Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to server and send email
        if email_config.smtp_use_tls:
            server = smtplib.SMTP(email_config.smtp_host, email_config.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP(email_config.smtp_host, email_config.smtp_port)
        
        if email_config.smtp_username and email_config.smtp_password:
            server.login(email_config.smtp_username, email_config.smtp_password)
        
        text = msg.as_string()
        server.sendmail(email_config.from_email, current_user.email, text)
        server.quit()
        
        return {"message": f"Test email sent successfully to {current_user.email}"}
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to send test email: {str(e)}"
        )


@router.get("/")
def get_all_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Get all settings organized by category (admin only).
    """
    categories = settings.get_all_categories(db)
    result = {}
    
    for category in categories:
        result[category] = settings.get_category_as_dict(db, category=category)
    
    return result


@router.post("/store/logo")
async def upload_store_logo(
    logo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Upload store logo (admin only).
    """
    try:
        # Delete old logo if it exists
        current_logo = settings.get_by_category_and_key(db, category="store", key="store_logo_url")
        if current_logo and current_logo.value:
            ImageService.delete_logo(current_logo.value)
        
        # Delete old favicon if it exists
        current_favicon = settings.get_by_category_and_key(db, category="store", key="store_favicon_url")
        if current_favicon and current_favicon.value:
            ImageService.delete_logo(current_favicon.value)
        
        # Upload new logo
        logo_url = await ImageService.save_store_logo(logo)
        
        # Generate favicon from logo
        favicon_url = await ImageService.generate_favicon_from_logo(logo_url)
        
        # Save both logo and favicon URLs to settings
        settings.upsert_setting(db, category="store", key="store_logo_url", value=logo_url)
        settings.upsert_setting(db, category="store", key="store_favicon_url", value=favicon_url)
        
        return {
            "message": "Logo uploaded successfully",
            "logo_url": logo_url,
            "favicon_url": favicon_url
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload logo: {str(e)}"
        )


@router.delete("/store/logo")
def delete_store_logo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Delete store logo and favicon (admin only).
    """
    try:
        # Get current logo
        current_logo = settings.get_by_category_and_key(db, category="store", key="store_logo_url")
        if current_logo and current_logo.value:
            # Delete logo file
            ImageService.delete_logo(current_logo.value)
            # Remove from settings
            settings.delete_by_category_and_key(db, category="store", key="store_logo_url")
        
        # Get current favicon
        current_favicon = settings.get_by_category_and_key(db, category="store", key="store_favicon_url")
        if current_favicon and current_favicon.value:
            # Delete favicon file
            ImageService.delete_logo(current_favicon.value)
            # Remove from settings
            settings.delete_by_category_and_key(db, category="store", key="store_favicon_url")
        
        return {"message": "Logo and favicon deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete logo: {str(e)}"
        ) 