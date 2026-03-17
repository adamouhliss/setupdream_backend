# Make.com WhatsApp Automation Setup

Automate WhatsApp order notifications using Make.com (free tier: 1,000 operations/month) 🚀

## 🎯 Complete Setup Guide

### Step 1: Create Make.com Account

1. **Visit**: https://www.make.com/en/register
2. **Sign up** for free account
3. **Verify** email address
4. **Login** to Make.com dashboard

### Step 2: Create WhatsApp Notification Scenario

#### 2.1 Start New Scenario
1. Click **"Create a new scenario"**
2. Search **"Webhooks"** and select it
3. Choose **"Custom webhook"**
4. Click **"Create a webhook"**
5. **Copy the webhook URL** (keep this safe!)

#### 2.2 Configure Webhook
1. Click **"OK"** to create the webhook
2. Leave webhook settings as default
3. The webhook is now waiting for data

### Step 3: Set Up WhatsApp Integration

#### Option A: WhatsApp Business API (Recommended)

1. **Add new module** (click the + button)
2. **Search** "WhatsApp Business"
3. **Select** "Send a Message"
4. **Create connection**:
   - You'll need WhatsApp Business API credentials
   - Or use a service like **360Dialog**, **Twilio**, or **MessageBird**

#### Option B: Use Twilio (Easier Setup)

1. **Add new module** after webhook
2. **Search** "Twilio"
3. **Select** "Send a WhatsApp Message"
4. **Create Twilio connection**:
   - Account SID (from Twilio console)
   - Auth Token (from Twilio console)
   - From number (Twilio WhatsApp number)

#### Option C: Use ChatAPI (Simple Alternative)

1. **Add new module**
2. **Search** "HTTP" → "Make a request"
3. **Configure HTTP request** for ChatAPI

### Step 4: Configure WhatsApp Message

#### 4.1 Map Webhook Data
In the WhatsApp module, configure:

**To (Phone Number):**
```
+212632253960
```

**Message Text:**
```
🎉 *NEW ORDER RECEIVED!*

📋 *Order #{{1.id}}*
👤 Customer: {{1.first_name}} {{1.last_name}}
📞 Phone: {{1.phone}}
📍 City: {{1.city}}

🛍️ *Items:*
{{1.items}}

💰 *Total: {{1.total}} MAD*

⏰ Order placed: {{1.created_at}}

🚚 Please contact customer to confirm delivery.

---
Carré Sports - Order Management
```

#### 4.2 Advanced Message Formatting (Optional)
For better item formatting, add an **Iterator** module:

1. **Add** "Iterator" module between webhook and WhatsApp
2. **Set Array**: `{{1.items}}`
3. **Format each item**: `{{item.productName}} (x{{item.quantity}}) - {{item.selectedColor}} - Size: {{item.selectedSize}}`

### Step 5: Test the Scenario

#### 5.1 Manual Test
1. **Click** "Run once" in Make.com
2. **Go to webhook settings**
3. **Click** "Determine data structure"
4. **Use sample JSON**:

```json
{
  "id": 123,
  "first_name": "Test",
  "last_name": "Customer", 
  "phone": "+212612345678",
  "city": "Casablanca",
  "items": [
    {
      "productName": "Nike Air Max",
      "quantity": 1,
      "selectedColor": "Black",
      "selectedSize": "42"
    }
  ],
  "total": 899.99,
  "payment_method": "cash",
  "created_at": "2024-07-13T10:30:00"
}
```

5. **Submit** sample data
6. **Check** if WhatsApp message is sent

#### 5.2 Save and Activate
1. **Save** the scenario
2. **Turn ON** the scenario (toggle switch)
3. **Copy** the webhook URL

### Step 6: Update Backend Configuration

Add the Make.com webhook URL to your environment:

```bash
# In your backend directory
echo "WHATSAPP_WEBHOOK_URL=YOUR_MAKE_WEBHOOK_URL" >> .env
```

Or manually add to `.env` file:
```env
# WhatsApp Notifications
ADMIN_WHATSAPP_NUMBER=+212632253960
WHATSAPP_WEBHOOK_URL=https://hook.make.com/your-webhook-id
```

### Step 7: Test Real Integration

1. **Restart** your FastAPI server
2. **Place a test order** through your frontend
3. **Check Make.com** execution log
4. **Verify** WhatsApp message received

## 🔧 Alternative WhatsApp Services

### Option 1: Twilio WhatsApp (Recommended)

**Setup:**
1. **Create** Twilio account: https://www.twilio.com
2. **Enable** WhatsApp sandbox
3. **Get** credentials:
   - Account SID
   - Auth Token
   - WhatsApp number (starts with `whatsapp:+14155238886`)

**Make.com Configuration:**
- Module: "Twilio" → "Send a WhatsApp Message"
- From: `whatsapp:+14155238886` (Twilio sandbox)
- To: `whatsapp:+212632253960` (your number)

### Option 2: Green API

**Setup:**
1. **Visit**: https://green-api.com
2. **Create** account and get API credentials
3. **Configure** WhatsApp instance

**Make.com Configuration:**
- Module: "HTTP" → "Make a request"
- URL: `https://api.green-api.com/waInstance{ID}/sendMessage/{TOKEN}`
- Method: POST
- Body:
```json
{
  "chatId": "212632253960@c.us",
  "message": "Your order message here"
}
```

### Option 3: ChatAPI

**Setup:**
1. **Visit**: https://chat-api.com
2. **Create** account
3. **Connect** your WhatsApp

**Make.com Configuration:**
- Module: "HTTP" → "Make a request"
- URL: `https://api.chat-api.com/instance{ID}/sendMessage`
- Headers: `Authorization: Bearer YOUR_TOKEN`

## 📊 Make.com Scenario Template

Here's a complete scenario structure:

```
Webhook → [Iterator] → WhatsApp Module → [Error Handler]
```

**Modules:**
1. **Webhooks**: Custom webhook (trigger)
2. **Iterator**: Process items array (optional)
3. **WhatsApp**: Send message
4. **Error Handler**: Log failures

## 🔍 Troubleshooting

### Webhook Not Receiving Data
```bash
# Test webhook manually
curl -X POST "YOUR_MAKE_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 999,
    "first_name": "Test",
    "last_name": "User",
    "phone": "+212612345678",
    "city": "Test City",
    "items": [{"productName": "Test Product", "quantity": 1}],
    "total": 299.99
  }'
```

### WhatsApp Messages Not Sending
1. **Check** WhatsApp connection in Make.com
2. **Verify** phone number format: `+212XXXXXXXXX`
3. **Test** with your own number first
4. **Check** Make.com execution log for errors

### Rate Limits
- **Make.com Free**: 1,000 operations/month
- **Twilio Sandbox**: 200 messages/day
- **Upgrade** plans available if needed

## 💰 Cost Breakdown

**Free Tier (Sufficient for Most Stores):**
- **Make.com**: 1,000 operations/month (FREE)
- **Twilio WhatsApp**: 200 messages/day (FREE sandbox)
- **Green API**: 1,000 messages/month (FREE)

**Paid Options:**
- **Make.com Pro**: $9/month (10,000 operations)
- **Twilio WhatsApp**: $0.005/message
- **WhatsApp Business API**: Variable pricing

## ✅ Final Checklist

- [ ] Make.com account created
- [ ] Webhook scenario created and activated  
- [ ] WhatsApp service connected (Twilio/Green API/etc.)
- [ ] Sample data tested successfully
- [ ] Backend environment updated with webhook URL
- [ ] Real order test completed
- [ ] WhatsApp message received

## 🚀 Ready to Go!

Your automated WhatsApp notifications are now set up! Every new order will trigger:

1. **Order created** in your FastAPI backend
2. **Webhook sent** to Make.com
3. **WhatsApp message** automatically sent to admin
4. **Order details** beautifully formatted

**Next Steps:**
1. Monitor Make.com executions
2. Customize message format as needed
3. Add more automation (email, SMS, etc.)
4. Scale up when you exceed free limits

🎉 **Congratulations! Your store now has professional automated order notifications!** 