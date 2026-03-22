from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, Tuple
from sqlalchemy.orm import Session
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import logging

from ...api.deps import get_db
from ...crud.settings import settings as settings_crud
from ...schemas.settings import StoreSettings

router = APIRouter()
logger = logging.getLogger(__name__)

def get_store_settings(db: Session) -> StoreSettings:
    """Get store settings from database with defaults"""
    settings_dict = settings_crud.get_category_as_dict(db, category="store")
    
    # Merge with defaults
    store_defaults = StoreSettings()
    for key, value in settings_dict.items():
        if hasattr(store_defaults, key):
            setattr(store_defaults, key, value)
    
    return store_defaults

# SMTP Configuration (will be made dynamic later)
SMTP_HOST = "smtp.nindomail.com"
SMTP_PORT = 465
SMTP_USERNAME = "info@setupdream.ma"
SMTP_PASSWORD = "Pocadils121!@"

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str
    language: Optional[str] = "fr"

def send_email(to_email: str, subject: str, body: str, from_email: str, is_html: bool = True):
    """Send email using SMTP"""
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        
        # Add body
        if is_html:
            part = MIMEText(body, "html", "utf-8")
        else:
            part = MIMEText(body, "plain", "utf-8")
        msg.attach(part)
        
        # Create SSL context
        context = ssl.create_default_context()
        
        # Send email
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(from_email, to_email, msg.as_string())
            
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def create_admin_email_template(form_data: ContactForm, store_settings: StoreSettings) -> Tuple[str, str]:
    """Create admin email template with dynamic store settings"""
    subject = f"🔔 New Contact Form Submission - {store_settings.store_name}"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #F59E0B, #D97706); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .field {{ margin-bottom: 20px; padding: 15px; background: white; border-radius: 5px; border-left: 4px solid #F59E0B; }}
            .label {{ font-weight: bold; color: #D97706; }}
            .value {{ margin-top: 5px; }}
            .urgent {{ background: #FEF2F2; border-left-color: #DC2626; }}
            .footer {{ text-align: center; margin-top: 30px; color: #6B7280; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🏪 {store_settings.store_name}</h2>
                <p>New Contact Form Submission</p>
            </div>
            <div class="content">
                <div class="field">
                    <div class="label">👤 From:</div>
                    <div class="value">{form_data.name}</div>
                </div>
                
                <div class="field">
                    <div class="label">📧 Email:</div>
                    <div class="value">{form_data.email}</div>
                </div>
                
                <div class="field">
                    <div class="label">📋 Subject:</div>
                    <div class="value">{form_data.subject}</div>
                </div>
                
                <div class="field urgent">
                    <div class="label">💬 Message:</div>
                    <div class="value">{form_data.message}</div>
                </div>
                
                <div class="field">
                    <div class="label">🌐 Language:</div>
                    <div class="value">{form_data.language.upper()}</div>
                </div>
                
                <div class="field">
                    <div class="label">⏰ Submitted:</div>
                    <div class="value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                
                <div class="footer">
                    <p><strong>📞 Reply to customer at:</strong> {form_data.email}</p>
                    <p><strong>🏪 {store_settings.store_name}</strong></p>
                    <p>📧 {store_settings.store_email} | 📞 {store_settings.store_phone}</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return subject, body

def create_customer_auto_reply_template(form_data: ContactForm, store_settings: StoreSettings) -> Tuple[str, str]:
    """Create auto-reply email template for customer with dynamic store settings"""
    if form_data.language == "fr":
        subject = f"✅ Votre message a été reçu - {store_settings.store_name}"
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #F59E0B, #D97706); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .highlight {{ background: #FEF3C7; padding: 15px; border-radius: 5px; border-left: 4px solid #F59E0B; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6B7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🏪 {store_settings.store_name}</h2>
                    <p>Merci pour votre message !</p>
                </div>
                <div class="content">
                    <p>Bonjour <strong>{form_data.name}</strong>,</p>
                    
                    <div class="highlight">
                        <p><strong>✅ Votre message a été reçu avec succès !</strong></p>
                        <p>Sujet : "{form_data.subject}"</p>
                    </div>
                    
                    <p>Nous vous remercions de nous avoir contactés. Notre équipe examine votre message et vous répondra dans les plus brefs délais, généralement sous 24 heures.</p>
                    
                    <p>Si votre demande est urgente, n'hésitez pas à nous appeler directement.</p>
                    
                    <div class="footer">
                        <p><strong>🏪 {store_settings.store_name}</strong></p>
                        <p>📧 {store_settings.store_email} | 📞 {store_settings.store_phone}</p>
                        <p>🌟 Votre partenaire pour l'équipement sportif premium</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        subject = f"✅ Your message has been received - {store_settings.store_name}"
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #F59E0B, #D97706); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .highlight {{ background: #FEF3C7; padding: 15px; border-radius: 5px; border-left: 4px solid #F59E0B; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6B7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🏪 {store_settings.store_name}</h2>
                    <p>Thank you for your message!</p>
                </div>
                <div class="content">
                    <p>Hello <strong>{form_data.name}</strong>,</p>
                    
                    <div class="highlight">
                        <p><strong>✅ Your message has been successfully received!</strong></p>
                        <p>Subject: "{form_data.subject}"</p>
                    </div>
                    
                    <p>Thank you for contacting us. Our team is reviewing your message and will respond as soon as possible, typically within 24 hours.</p>
                    
                    <p>If your inquiry is urgent, please don't hesitate to call us directly.</p>
                    
                    <div class="footer">
                        <p><strong>🏪 {store_settings.store_name}</strong></p>
                        <p>📧 {store_settings.store_email} | 📞 {store_settings.store_phone}</p>
                        <p>🌟 Your premium sports equipment partner</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    return subject, body

@router.post("/send")
async def send_contact_form(form_data: ContactForm, db: Session = Depends(get_db)):
    """Handle contact form submission"""
    try:
        logger.info(f"Processing contact form from {form_data.email}")
        
        # Get store settings
        store_settings = get_store_settings(db)
        
        # Send notification to admin
        admin_subject, admin_body = create_admin_email_template(form_data, store_settings)
        admin_sent = send_email(store_settings.store_email, admin_subject, admin_body, store_settings.store_email, is_html=True)
        
        # Send auto-reply to customer  
        reply_subject, reply_body = create_customer_auto_reply_template(form_data, store_settings)
        reply_sent = send_email(form_data.email, reply_subject, reply_body, store_settings.store_email, is_html=True)
        
        if admin_sent and reply_sent:
            return {
                "success": True, 
                "message": "Contact form sent successfully! We'll get back to you soon." if form_data.language == "en" else "Formulaire de contact envoyé avec succès ! Nous vous répondrons bientôt.",
                "admin_notified": True,
                "auto_reply_sent": True
            }
        elif admin_sent:
            return {
                "success": True,
                "message": "Contact form sent successfully!" if form_data.language == "en" else "Formulaire de contact envoyé avec succès !",
                "admin_notified": True, 
                "auto_reply_sent": False
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email. Please try again later." if form_data.language == "en" else "Échec de l'envoi de l'email. Veuillez réessayer plus tard."
            )
            
    except Exception as e:
        logger.error(f"Contact form error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending your message. Please try again." if form_data.language == "en" else "Une erreur s'est produite lors de l'envoi de votre message. Veuillez réessayer."
        )

@router.post("/test-email")
async def test_email(db: Session = Depends(get_db)):
    """Test email sending functionality"""
    logger.info("Testing email functionality")
    
    try:
        # Get store settings for test
        store_settings = get_store_settings(db)
        
        test_form = ContactForm(
            name="Test User",
            email="test@example.com",
            subject="Test Email",
            message="This is a test message to verify email functionality.",
            language="en"
        )
        
        admin_subject, admin_body = create_admin_email_template(test_form, store_settings)
        result = send_email(store_settings.store_email, admin_subject, admin_body, store_settings.store_email, is_html=True)
        
        return {
            "success": result,
            "message": "Test email sent!" if result else "Failed to send test email",
            "smtp_host": SMTP_HOST,
            "smtp_port": SMTP_PORT,
            "from_email": store_settings.store_email
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        } 