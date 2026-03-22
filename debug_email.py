#!/usr/bin/env python3
"""
Advanced email debugging for Setup Dream contact form
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import socket

# Your SMTP Configuration
SMTP_HOST = "smtp.nindomail.com"
SMTP_PORT = 465
SMTP_USERNAME = "info@Setupdream.ma"
SMTP_PASSWORD = "Pocadils121!@"
FROM_EMAIL = "info@Setupdream.ma"
TO_EMAIL = "info@Setupdream.ma"

def test_smtp_connection():
    """Test SMTP connection step by step"""
    print("🔍 DETAILED SMTP DEBUGGING")
    print("=" * 50)
    
    # Test 1: DNS Resolution
    try:
        print(f"🌐 Testing DNS resolution for {SMTP_HOST}...")
        ip = socket.gethostbyname(SMTP_HOST)
        print(f"✅ DNS OK - {SMTP_HOST} resolves to {ip}")
    except Exception as e:
        print(f"❌ DNS FAILED: {e}")
        return False
    
    # Test 2: Port Connection
    try:
        print(f"🔌 Testing port connection to {SMTP_HOST}:{SMTP_PORT}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((SMTP_HOST, SMTP_PORT))
        sock.close()
        if result == 0:
            print(f"✅ Port connection OK")
        else:
            print(f"❌ Port connection FAILED - Error code: {result}")
            return False
    except Exception as e:
        print(f"❌ Port test FAILED: {e}")
        return False
    
    # Test 3: SMTP SSL Connection
    try:
        print(f"🔐 Testing SMTP SSL connection...")
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=30)
        server.set_debuglevel(1)  # Enable debug output
        print(f"✅ SMTP SSL connection established")
        
        # Test 4: Authentication
        print(f"🔑 Testing authentication...")
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        print(f"✅ Authentication successful")
        
        # Test 5: Send simple email
        print(f"📧 Sending test email...")
        
        msg = MIMEText("This is a simple test email from Setup Dream contact form debugging.", "plain", "utf-8")
        msg["Subject"] = "🔧 SMTP Debug Test - Setup Dream"
        msg["From"] = FROM_EMAIL
        msg["To"] = TO_EMAIL
        
        server.sendmail(FROM_EMAIL, [TO_EMAIL], msg.as_string())
        print(f"✅ Email sent successfully")
        
        server.quit()
        print(f"✅ SMTP session closed properly")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ AUTHENTICATION FAILED: {e}")
        print("🔍 Check username/password")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        print(f"❌ RECIPIENT REFUSED: {e}")
        print("🔍 Check recipient email address")
        return False
    except smtplib.SMTPSenderRefused as e:
        print(f"❌ SENDER REFUSED: {e}")
        print("🔍 Check sender email address")
        return False
    except Exception as e:
        print(f"❌ SMTP ERROR: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        return False

def test_alternative_smtp_settings():
    """Test alternative SMTP configurations"""
    print("\n🔄 TRYING ALTERNATIVE SMTP CONFIGURATIONS")
    print("=" * 50)
    
    alternative_configs = [
        {"host": "smtp.nindomail.com", "port": 587, "use_tls": True, "name": "Port 587 with STARTTLS"},
        {"host": "smtp.nindomail.com", "port": 25, "use_tls": False, "name": "Port 25 without encryption"},
        {"host": "mail.nindomail.com", "port": 465, "use_tls": False, "name": "mail.nindomail.com SSL"},
    ]
    
    for config in alternative_configs:
        print(f"\n🧪 Testing: {config['name']}")
        print(f"   Host: {config['host']}:{config['port']}")
        
        try:
            if config.get('use_tls'):
                # Use STARTTLS
                server = smtplib.SMTP(config['host'], config['port'], timeout=15)
                server.starttls()
            elif config['port'] == 465:
                # Use SSL
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(config['host'], config['port'], context=context, timeout=15)
            else:
                # Plain connection
                server = smtplib.SMTP(config['host'], config['port'], timeout=15)
            
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            print(f"   ✅ {config['name']} - Login successful!")
            
            # Send quick test
            msg = MIMEText(f"Test from {config['name']}", "plain")
            msg["Subject"] = f"Alternative SMTP Test - {config['name']}"
            msg["From"] = FROM_EMAIL
            msg["To"] = TO_EMAIL
            
            server.sendmail(FROM_EMAIL, [TO_EMAIL], msg.as_string())
            print(f"   ✅ {config['name']} - Email sent!")
            
            server.quit()
            return config  # Return successful config
            
        except Exception as e:
            print(f"   ❌ {config['name']} - Failed: {e}")
    
    return None

if __name__ == "__main__":
    print("🧪 ADVANCED EMAIL DEBUGGING - Setup Dream")
    print("=" * 60)
    
    # Test current configuration
    success = test_smtp_connection()
    
    if not success:
        print("\n⚠️  Current configuration failed. Trying alternatives...")
        alternative = test_alternative_smtp_settings()
        
        if alternative:
            print(f"\n✅ WORKING CONFIGURATION FOUND:")
            print(f"   Host: {alternative['host']}")
            print(f"   Port: {alternative['port']}")
            print(f"   Method: {alternative['name']}")
        else:
            print(f"\n❌ ALL CONFIGURATIONS FAILED")
            print(f"\n🔍 TROUBLESHOOTING STEPS:")
            print(f"1. Verify SMTP credentials with your hosting provider")
            print(f"2. Check if SMTP is enabled for your email account")
            print(f"3. Try accessing your email via webmail to confirm login")
            print(f"4. Contact your hosting provider (nindomail.com) for SMTP settings")
    else:
        print(f"\n🎉 EMAIL SYSTEM IS WORKING!")
        print(f"📬 Check your inbox: {TO_EMAIL}")
        print(f"📁 Also check SPAM folder")
    
    print("=" * 60) 