#!/usr/bin/env python3
"""
Simple Make.com Webhook Tester
==============================

Quick test for your Make.com webhook - no environment setup needed!
"""

import requests
import json
from datetime import datetime

def test_webhook():
    """Test Make.com webhook with sample order"""
    
    # Your webhook URL
    webhook_url = "https://hook.eu2.make.com/hv4vjnbpy16qe437drh642pu5srknrw4"
    
    # Sample order data
    test_order = {
        "id": 777,
        "first_name": "Youssef",
        "last_name": "Alami",
        "phone": "+212661234567",
        "city": "Casablanca",
        "items": "Nike Air Jordan (x1) - White/Black - Size: 43",
        "total": 1599.99,
        "payment_method": "cash",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    print("🧪 Testing Make.com Webhook")
    print("=" * 30)
    print(f"📤 Webhook: {webhook_url}")
    print(f"📋 Order ID: {test_order['id']}")
    print(f"👤 Customer: {test_order['first_name']} {test_order['last_name']}")
    print(f"💰 Total: {test_order['total']} MAD")
    print()
    
    try:
        print("⏳ Sending webhook...")
        response = requests.post(
            webhook_url,
            json=test_order,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! Webhook accepted")
            print("📱 Check your Make.com execution log")
            print("💬 Check WhatsApp for notification")
            return True
        elif response.status_code == 401:
            print("❌ 401 Unauthorized")
            print("💡 Your Make.com scenario needs setup:")
            print("   1. Add Twilio WhatsApp module")
            print("   2. Configure webhook data structure")
            print("   3. Save and activate scenario")
            return False
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout (this might be normal)")
        print("💡 Check Make.com execution log")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Setup dream - Webhook Tester")
    print("=" * 35)
    print()
    
    success = test_webhook()
    
    print("\n" + "="*40)
    if success:
        print("🎉 WEBHOOK TEST PASSED!")
        print("\n📋 Next steps:")
        print("1. Set up your .env file with webhook URL")
        print("2. Test a real order through your frontend")
        print("3. Verify WhatsApp notifications work")
    else:
        print("⚠️ WEBHOOK NEEDS SETUP")
        print("\n🔧 Follow the Twilio guide:")
        print("1. Create Twilio account")
        print("2. Set up WhatsApp sandbox") 
        print("3. Configure Make.com with Twilio module")
        print("4. Test again")
    
    print("\n📚 See: TWILIO_WHATSAPP_SETUP.md for detailed guide") 