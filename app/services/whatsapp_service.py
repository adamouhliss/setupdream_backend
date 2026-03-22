import logging
import os
from typing import Optional
import asyncio
from datetime import datetime
import json

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Alternative webhook approach for production (recommended)
import requests

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self):
        self.admin_phone = os.getenv("ADMIN_WHATSAPP_NUMBER", "")  # Format: +212XXXXXXXXX
        self.webhook_url = os.getenv("WHATSAPP_WEBHOOK_URL", "")  # Optional webhook URL
        self.enabled = bool(self.admin_phone)
        
        if not self.enabled:
            logger.warning("WhatsApp notifications disabled: No admin phone number configured")
    
    def format_phone_number(self, phone: str) -> str:
        """Format phone number for WhatsApp (must include country code)"""
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # If it starts with 212 (Morocco), keep as is
        if digits.startswith('212'):
            return f"+{digits}"
        
        # If it starts with 0, replace with 212
        if digits.startswith('0'):
            return f"+212{digits[1:]}"
        
        # Otherwise, assume it needs 212 prefix
        return f"+212{digits}"
    
    def create_order_message(self, order_data: dict) -> str:
        """Create a formatted WhatsApp message for new orders"""
        try:
            customer_name = f"{order_data.get('first_name', '')} {order_data.get('last_name', '')}".strip()
            total_amount = order_data.get('total', 0)
            items_count = len(order_data.get('items', []))
            phone = order_data.get('phone', '')
            city = order_data.get('city', '')
            
            # Format items list
            items_text = ""
            for i, item in enumerate(order_data.get('items', [])[:3], 1):  # Show first 3 items
                item_name = item.get('productName', 'Unknown Product')
                quantity = item.get('quantity', 1)
                size = item.get('selectedSize', '')
                color = item.get('selectedColor', '')
                
                item_details = f"{item_name} (x{quantity})"
                if color:
                    item_details += f" - {color}"
                if size:
                    item_details += f" - Size: {size}"
                
                items_text += f"{i}. {item_details}\n"
            
            if len(order_data.get('items', [])) > 3:
                items_text += f"...and {len(order_data.get('items', [])) - 3} more items\n"
            
            message = f"""🎉 *NEW ORDER RECEIVED!*

📋 *Order #{order_data.get('id', 'N/A')}*
👤 Customer: {customer_name}
📞 Phone: {phone}
📍 City: {city}

🛍️ *Items ({items_count}):*
{items_text}
💰 *Total: {total_amount:.2f} MAD*

⏰ Order placed: {datetime.now().strftime('%d/%m/%Y at %H:%M')}

🚚 Please contact the customer to confirm delivery details.

---
Setup dream - Order Management"""
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating order message: {e}")
            return f"New order received - Order #{order_data.get('id', 'N/A')} from {customer_name}. Total: {total_amount:.2f} MAD"
    
    async def send_order_notification_async(self, order_data: dict) -> bool:
        """Send WhatsApp notification asynchronously"""
        if not self.enabled:
            logger.info("WhatsApp notifications disabled")
            return False
        
        try:
            message = self.create_order_message(order_data)
            admin_phone = self.format_phone_number(self.admin_phone)
            
            # Try webhook method (recommended for production)
            if self.webhook_url:
                success = await self._send_via_webhook(admin_phone, message, order_data)
                if success:
                    return True
            
            # For free alternatives, log the message and suggest manual setup
            logger.info("=== NEW ORDER NOTIFICATION ===")
            logger.info(f"Send this message to {admin_phone}:")
            logger.info(message)
            logger.info("=== END NOTIFICATION ===")
            
            # You can also save to a file for manual checking
            self._save_notification_to_file(message, admin_phone)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp notification: {e}")
            return False
    
    def send_order_notification(self, order_data: dict) -> bool:
        """Send WhatsApp notification synchronously"""
        try:
            # Run async function in sync context
            return asyncio.run(self.send_order_notification_async(order_data))
        except Exception as e:
            logger.error(f"Error in sync WhatsApp notification: {e}")
            return False
    
    async def _send_via_webhook(self, phone: str, message: str, order_data: dict = None) -> bool:
        """Send order notification via webhook (Make.com/Telegram integration)"""
        try:
            # Send complete order data that Make.com expects for Telegram notifications
            if order_data:
                # Format items for better display
                items_text = ""
                for item in order_data.get('items', []):
                    if isinstance(item, dict):
                        product_name = item.get('productName', 'Product')
                        quantity = item.get('quantity', 1)
                        color = item.get('selectedColor', '')
                        size = item.get('selectedSize', '')
                        
                        item_line = f"{product_name} (x{quantity})"
                        if color:
                            item_line += f" - {color}"
                        if size:
                            item_line += f" - Size: {size}"
                        items_text += item_line + "\n"
                
                # Prepare webhook payload in the format Make.com expects
                payload = {
                    "id": order_data.get('id'),
                    "first_name": order_data.get('first_name', ''),
                    "last_name": order_data.get('last_name', ''),
                    "phone": order_data.get('phone', ''),
                    "city": order_data.get('city', ''),
                    "items": items_text.strip(),
                    "total": order_data.get('total', 0),
                    "payment_method": order_data.get('payment_method', ''),
                    "created_at": order_data.get('created_at', '')
                }
            else:
                # Fallback to simple message format
                payload = {
                    "phone": phone,
                    "message": message,
                    "type": "notification"
                }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"Order notification sent via webhook (Telegram) for order #{payload.get('id', 'unknown')}")
                return True
            else:
                logger.error(f"Webhook failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Webhook send error: {e}")
            return False
    
    def _save_notification_to_file(self, message: str, phone: str):
        """Save notification to file for manual checking"""
        try:
            notifications_file = "whatsapp_notifications.txt"
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(notifications_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"To: {phone}\n")
                f.write(f"Message:\n{message}\n")
                f.write(f"{'='*50}\n")
            
            logger.info(f"Notification saved to {notifications_file}")
        except Exception as e:
            logger.error(f"Error saving notification to file: {e}")
    
    def test_connection(self) -> dict:
        """Test WhatsApp service configuration"""
        result = {
            "enabled": self.enabled,
            "admin_phone": self.admin_phone if self.admin_phone else "Not configured",
            "webhook_configured": bool(self.webhook_url),
            "status": "❌ Not configured"
        }
        
        if self.enabled:
            if self.webhook_url:
                result["status"] = "✅ Webhook configured"
            else:
                result["status"] = "✅ File/Log notifications active (manual WhatsApp)"
        
        return result
    
    def send_test_notification(self) -> bool:
        """Send a test notification to verify the setup"""
        try:
            # Create test order data in the format expected by Make.com/Telegram
            test_order = {
                "id": 999,
                "first_name": "Test",
                "last_name": "Customer",
                "phone": "+212612345678",
                "city": "Test City",
                "items": [
                    {
                        "productName": "Nike Test Product",
                        "quantity": 1,
                        "selectedColor": "Black",
                        "selectedSize": "42"
                    }
                ],
                "total": 999.99,
                "payment_method": "cash",
                "created_at": datetime.now().isoformat()
            }
            
            message = self.create_order_message(test_order)
            
            if self.webhook_url:
                # Test webhook with complete order data
                import requests
                
                # Format items for webhook
                items_text = ""
                for item in test_order.get('items', []):
                    product_name = item.get('productName', 'Product')
                    quantity = item.get('quantity', 1)
                    color = item.get('selectedColor', '')
                    size = item.get('selectedSize', '')
                    
                    item_line = f"{product_name} (x{quantity})"
                    if color:
                        item_line += f" - {color}"
                    if size:
                        item_line += f" - Size: {size}"
                    items_text += item_line + "\n"
                
                payload = {
                    "id": test_order.get('id'),
                    "first_name": test_order.get('first_name', ''),
                    "last_name": test_order.get('last_name', ''),
                    "phone": test_order.get('phone', ''),
                    "city": test_order.get('city', ''),
                    "items": items_text.strip(),
                    "total": test_order.get('total', 0),
                    "payment_method": test_order.get('payment_method', ''),
                    "created_at": test_order.get('created_at', '')
                }
                
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info("Test notification sent via webhook (Telegram)")
                    return True
                else:
                    logger.error(f"Test webhook failed: {response.status_code}")
                    
            # Fallback: save to file for testing
            self._save_notification_to_file(message, self.admin_phone)
            logger.info("Test notification saved to file")
            return True
            
        except Exception as e:
            logger.error(f"Error sending test notification: {e}")
            return False


# Global instance
whatsapp_service = WhatsAppService() 