#!/usr/bin/env python3
"""
WhatsApp Notification Setup for Setup dream
============================================

This script helps you set up WhatsApp notifications for new orders.
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create or update .env file with WhatsApp configuration"""
    env_file = Path(".env")
    
    print("🔧 WhatsApp Notification Setup")
    print("=" * 40)
    
    # Get admin phone number
    print("\n📱 Admin WhatsApp Number:")
    print("Enter the admin's WhatsApp number (with country code)")
    print("Examples: +212612345678, +33123456789, +1234567890")
    
    admin_phone = input("Admin WhatsApp Number: ").strip()
    
    if not admin_phone:
        print("❌ Phone number is required!")
        return False
    
    # Format phone number
    if not admin_phone.startswith('+'):
        if admin_phone.startswith('0'):
            admin_phone = f"+212{admin_phone[1:]}"  # Assume Morocco if starts with 0
        elif admin_phone.startswith('212'):
            admin_phone = f"+{admin_phone}"
        else:
            admin_phone = f"+212{admin_phone}"  # Default to Morocco
    
    print(f"✅ Formatted number: {admin_phone}")
    
    # Optional webhook URL
    print("\n🔗 Webhook URL (Optional):")
    print("If you have a WhatsApp webhook service, enter the URL.")
    print("Leave empty to use pywhatkit (requires WhatsApp Web)")
    
    webhook_url = input("Webhook URL (optional): ").strip()
    
    # Read existing .env file
    existing_env = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    existing_env[key.strip()] = value.strip()
    
    # Update with WhatsApp config
    existing_env['ADMIN_WHATSAPP_NUMBER'] = admin_phone
    if webhook_url:
        existing_env['WHATSAPP_WEBHOOK_URL'] = webhook_url
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.write("# Setup dream Environment Configuration\n")
        f.write("# =====================================\n\n")
        
        # Database config
        if 'DATABASE_URL' in existing_env:
            f.write("# Database\n")
            f.write(f"DATABASE_URL={existing_env['DATABASE_URL']}\n\n")
        
        # App config
        if 'SECRET_KEY' in existing_env:
            f.write("# App Security\n")
            f.write(f"SECRET_KEY={existing_env['SECRET_KEY']}\n\n")
        
        # WhatsApp config
        f.write("# WhatsApp Notifications\n")
        f.write(f"ADMIN_WHATSAPP_NUMBER={admin_phone}\n")
        if webhook_url:
            f.write(f"WHATSAPP_WEBHOOK_URL={webhook_url}\n")
        f.write("\n")
        
        # Write remaining vars
        whatsapp_vars = {'ADMIN_WHATSAPP_NUMBER', 'WHATSAPP_WEBHOOK_URL'}
        special_vars = {'DATABASE_URL', 'SECRET_KEY'} | whatsapp_vars
        
        other_vars = {k: v for k, v in existing_env.items() if k not in special_vars}
        if other_vars:
            f.write("# Other Configuration\n")
            for key, value in other_vars.items():
                f.write(f"{key}={value}\n")
    
    print(f"✅ Configuration saved to {env_file}")
    return True

def test_whatsapp_service():
    """Test WhatsApp service configuration"""
    print("\n🧪 Testing WhatsApp Service")
    print("=" * 30)
    
    try:
        # Set environment variables from .env
        from dotenv import load_dotenv
        load_dotenv()
        
        from app.services.whatsapp_service import whatsapp_service
        
        status = whatsapp_service.test_connection()
        
        print(f"📱 Admin Phone: {status['admin_phone']}")
        print(f"🔧 Status: {status['status']}")
        print(f"📦 Pywhatkit Available: {status['pywhatkit_available']}")
        print(f"🔗 Webhook Configured: {status['webhook_configured']}")
        
        if status['enabled']:
            print("\n✅ WhatsApp notifications are configured!")
            
            # Test message option
            send_test = input("\nSend test message? (y/n): ").lower().strip()
            if send_test == 'y':
                test_order_data = {
                    "id": 999,
                    "first_name": "Test",
                    "last_name": "Customer",
                    "phone": "+212612345678",
                    "city": "Casablanca",
                    "items": [
                        {"productName": "Test Product", "quantity": 1}
                    ],
                    "total": 299.99
                }
                
                print("📤 Sending test notification...")
                success = whatsapp_service.send_order_notification(test_order_data)
                
                if success:
                    print("✅ Test notification sent successfully!")
                else:
                    print("❌ Test notification failed. Check logs for details.")
        else:
            print("❌ WhatsApp notifications are not configured properly")
            print("Please run the setup again or check your configuration")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install required packages: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error testing WhatsApp service: {e}")

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing WhatsApp Dependencies")
    print("=" * 35)
    
    packages = [
        "pywhatkit==5.4",
        "requests==2.31.0",
        "selenium==4.15.2",
        "python-dotenv==1.0.0"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        exit_code = os.system(f"pip install {package}")
        if exit_code != 0:
            print(f"❌ Failed to install {package}")
            return False
    
    print("✅ All dependencies installed successfully!")
    return True

def main():
    """Main setup function"""
    print("🎉 Welcome to Setup dream WhatsApp Setup!")
    print("=" * 45)
    
    print("\nThis script will help you configure WhatsApp notifications")
    print("for new orders. You'll need:")
    print("• Admin's WhatsApp number")
    print("• Optional: Webhook URL for production")
    print()
    
    # Check if we should install dependencies
    try:
        import pywhatkit
        import requests
    except ImportError:
        print("📦 Installing required dependencies...")
        if not install_dependencies():
            print("❌ Failed to install dependencies. Please install manually:")
            print("pip install pywhatkit requests selenium python-dotenv")
            return
    
    # Create/update environment configuration
    if not create_env_file():
        print("❌ Setup failed!")
        return
    
    # Test the configuration
    test_whatsapp_service()
    
    print("\n🎯 Next Steps:")
    print("=" * 15)
    print("1. Restart your FastAPI server")
    print("2. For pywhatkit: Make sure WhatsApp Web is logged in on the server")
    print("3. Place a test order to verify notifications work")
    print("4. Check server logs for any issues")
    print()
    print("📋 API Test Endpoint:")
    print("GET /api/v1/orders/test/whatsapp-status (admin only)")
    print()
    print("✅ Setup completed!")

if __name__ == "__main__":
    main() 