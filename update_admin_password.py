#!/usr/bin/env python3
"""
Create or update admin user with secure password
"""
import sys
import os
from sqlalchemy.orm import Session

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.user import User
from app.crud.user import user as user_crud
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

def update_admin_password():
    """Create or update admin user with secure password"""
    print("🔐 ADMIN PASSWORD SECURITY UPDATE")
    print("=" * 50)
    
    # Get database session
    db: Session = SessionLocal()
    
    try:
        # Check if admin user exists
        admin_user = user_crud.get_by_email(db, email=settings.FIRST_SUPERUSER)
        
        if admin_user:
            print(f"👤 Found existing admin user: {settings.FIRST_SUPERUSER}")
            
            # Update password
            new_password_hash = get_password_hash(settings.FIRST_SUPERUSER_PASSWORD)
            admin_user.hashed_password = new_password_hash
            
            # Ensure admin privileges
            admin_user.is_superuser = True
            admin_user.is_active = True
            admin_user.is_verified = True
            
            db.commit()
            db.refresh(admin_user)
            
            print("✅ Admin password updated successfully!")
            print("🔐 New password hash set")
            print("👑 Superuser privileges confirmed")
            
        else:
            print(f"👤 Admin user not found. Creating: {settings.FIRST_SUPERUSER}")
            
            # Create new admin user
            admin_data = UserCreate(
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                first_name="Admin",
                last_name="Setup dream",
                is_active=True,
                is_superuser=True,
                is_verified=True
            )
            
            admin_user = user_crud.create(db, obj_in=admin_data)
            admin_user.is_superuser = True
            admin_user.is_verified = True
            db.commit()
            db.refresh(admin_user)
            
            print("✅ Admin user created successfully!")
            print("👑 Superuser privileges granted")
        
        print()
        print("🔐 ADMIN LOGIN CREDENTIALS:")
        print("=" * 30)
        print(f"📧 Email: {settings.FIRST_SUPERUSER}")
        print(f"🔑 Password: {settings.FIRST_SUPERUSER_PASSWORD}")
        print()
        print("⚠️  IMPORTANT SECURITY NOTES:")
        print("• This password is much stronger than the previous 'admin123'")
        print("• Store this password in a secure location")
        print("• Consider changing it again after first login")
        print("• Use this to access the admin panel on your website")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    finally:
        db.close()

def test_admin_login():
    """Test admin login with new password"""
    print("\n🧪 TESTING ADMIN LOGIN")
    print("=" * 25)
    
    db: Session = SessionLocal()
    
    try:
        # Test authentication
        admin_user = user_crud.authenticate(
            db, 
            email=settings.FIRST_SUPERUSER, 
            password=settings.FIRST_SUPERUSER_PASSWORD
        )
        
        if admin_user:
            print("✅ Admin login test: SUCCESS")
            print(f"👤 User ID: {admin_user.id}")
            print(f"👑 Is Superuser: {admin_user.is_superuser}")
            print(f"✅ Is Active: {admin_user.is_active}")
            return True
        else:
            print("❌ Admin login test: FAILED")
            print("🔍 Check password hash or authentication logic")
            return False
            
    except Exception as e:
        print(f"❌ Login test ERROR: {e}")
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting Admin Security Update...")
    print()
    
    success = update_admin_password()
    
    if success:
        test_success = test_admin_login()
        
        if test_success:
            print("\n🎉 ADMIN SECURITY UPDATE COMPLETE!")
            print("🔐 Your admin account is now secured with a strong password")
            print("🌐 You can now login to your website admin panel")
        else:
            print("\n⚠️  Admin user updated but login test failed")
            print("🔧 You may need to debug the authentication system")
    else:
        print("\n❌ Admin security update failed")
        print("🔧 Check database connection and permissions") 