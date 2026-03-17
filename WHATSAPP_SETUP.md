# WhatsApp Order Notifications Setup

Get instant WhatsApp notifications when customers place new orders! 🎉

## Quick Setup (3 minutes)

### 1. Install Dependencies
```bash
cd backend
pip install pywhatkit requests selenium python-dotenv
```

### 2. Run Setup Script
```bash
python setup_whatsapp.py
```

### 3. Configure Environment
The script will ask for:
- **Admin WhatsApp Number**: Your WhatsApp number (e.g., +212612345678)
- **Webhook URL** (optional): Leave empty for free setup

### 4. Start Server
```bash
uvicorn app.main:app --reload
```

## Free Method (pywhatkit)

### Requirements:
- Chrome browser installed
- WhatsApp Web logged in
- Admin phone number configured

### How it works:
1. Opens WhatsApp Web automatically
2. Sends formatted order notification
3. Closes browser tab

### Setup WhatsApp Web:
1. Open https://web.whatsapp.com in Chrome
2. Scan QR code with your phone
3. Stay logged in

## Production Method (webhook)

For production, use a webhook service like:
- **Twilio WhatsApp API** (has free tier)
- **WhatsApp Business API**
- **Custom webhook service**

Set `WHATSAPP_WEBHOOK_URL` in your `.env` file.

## Environment Variables

Add to your `.env` file:
```env
# WhatsApp Notifications
ADMIN_WHATSAPP_NUMBER=+212612345678
WHATSAPP_WEBHOOK_URL=https://your-webhook.com/whatsapp
```

## Testing

### 1. Test API Endpoint
```bash
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     http://localhost:8000/api/v1/orders/test/whatsapp-status
```

### 2. Place Test Order
- Go to your frontend
- Add items to cart
- Complete checkout
- Check WhatsApp for notification

### 3. Check Logs
```bash
# View server logs for WhatsApp status
tail -f backend.log
```

## Message Format

The notification includes:
```
🎉 NEW ORDER RECEIVED!

📋 Order #123
👤 Customer: John Doe  
📞 Phone: +212612345678
📍 City: Casablanca

🛍️ Items (2):
1. Nike Air Max (x1)
2. Adidas T-Shirt (x2)

💰 Total: 899.99 MAD

⏰ Order placed: 15/07/2024 at 14:30

🚚 Please contact the customer to confirm delivery details.

---
Carré Sports - Order Management
```

## Troubleshooting

### "pywhatkit not found"
```bash
pip install pywhatkit==5.4
```

### "WhatsApp Web not logged in"
1. Open Chrome manually
2. Go to https://web.whatsapp.com  
3. Scan QR code
4. Try again

### "Phone number invalid"
- Use international format: +212612345678
- Include country code
- No spaces or special characters

### "Selenium errors"
```bash
pip install selenium==4.15.2
# Install Chrome browser if missing
```

## Railway Deployment

For Railway deployment, add environment variables:

```bash
# In Railway dashboard
ADMIN_WHATSAPP_NUMBER=+212612345678
WHATSAPP_WEBHOOK_URL=https://your-webhook.com/whatsapp
```

**Note**: pywhatkit won't work on Railway (no browser). Use webhook method for production.

## Security Notes

- Never commit phone numbers to git
- Use environment variables only
- Test with your own number first
- Monitor for spam/rate limits

## Free Alternatives

1. **Email notifications** (always free)
2. **Telegram bot** (free API)
3. **Discord webhook** (free)
4. **Slack webhook** (free)

## Support

If you need help:
1. Check server logs
2. Test the API endpoint
3. Verify WhatsApp Web login
4. Try with a different phone number

✅ **Ready to receive order notifications!** 