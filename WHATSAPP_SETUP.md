# WhatsApp Business API Setup Guide

## Option 1: Meta WhatsApp Business Cloud API (Recommended – Free Tier Available)

### Step 1: Create Meta Developer Account
1. Go to https://developers.facebook.com
2. Create account or log in
3. Create a new App → Business → Continue

### Step 2: Add WhatsApp Product
1. In your app dashboard: Add Product → WhatsApp → Set Up
2. You'll get a test phone number and API token immediately

### Step 3: Get your credentials
From the WhatsApp > Getting Started panel:
- **Phone Number ID** → WHATSAPP_PHONE_NUMBER_ID in .env
- **Temporary Access Token** → WHATSAPP_API_TOKEN in .env
  (For production, generate a permanent System User token in Business Manager)

### Step 4: Send a test message
```bash
curl -X POST https://graph.facebook.com/v19.0/YOUR_PHONE_NUMBER_ID/messages \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","to":"233241234567","type":"text","text":{"body":"Test"}}'
```

### Step 5: Configure Webhook (for receiving replies)
1. WhatsApp > Configuration > Webhook
2. Callback URL: https://yourdomain.com/webhook/whatsapp/
3. Verify Token: (same as WHATSAPP_VERIFY_TOKEN in .env)
4. Subscribe to: messages

### Step 6: Register speakers' numbers
Each speaker must message your WhatsApp Business number first 
(required by Meta for user-initiated conversations).
OR use approved Message Templates for business-initiated messages.

## Speaker Phone Number Format
Numbers MUST be in international format WITHOUT + or spaces:
- Ghana: 233241234567 (not +233 24 123 4567)
- Nigeria: 2348012345678
- Kenya: 254712345678

## Free Tier Limits
- 1,000 free conversations/month per phone number
- More than enough for a church!
- Upgrade to paid for higher volume

## Option 2: Twilio WhatsApp (Alternative)
1. Sign up at twilio.com
2. Activate WhatsApp Sandbox or get a business number
3. Update sermons/whatsapp.py to use Twilio client library
