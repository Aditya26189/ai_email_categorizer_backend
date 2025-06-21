# Gmail Webhook Setup Guide

## 🔧 **Environment Variables**

Add these to your `.env` file:

```env
# Gmail Webhook Configuration
GMAIL_PROJECT_ID=second-sandbox-463119-k3
GMAIL_WEBHOOK_TOPIC=gmail-events
```

## 🚀 **Google Cloud Pub/Sub Setup**

### **1. Create the Pub/Sub Topic**

```bash
# Create the Gmail webhook topic
gcloud pubsub topics create gmail-events \
  --project=second-sandbox-463119-k3
```

### **2. Create a Push Subscription**

```bash
# Create subscription that pushes to your webhook
gcloud pubsub subscriptions create gmail-events-sub \
  --topic=gmail-events \
  --push-endpoint=https://your-domain.com/webhook/gmail \
  --project=second-sandbox-463119-k3
```

### **3. For Development (ngrok)**

If you're using ngrok for development:

```bash
# Start ngrok
ngrok http 8000

# Update subscription with ngrok URL
gcloud pubsub subscriptions update gmail-events-sub \
  --push-endpoint=https://your-ngrok-url.ngrok.io/webhook/gmail \
  --project=second-sandbox-463119-k3
```

## 📋 **Topic Structure**

Your topic will be: `projects/second-sandbox-463119-k3/topics/gmail-events`

**Full topic name:** `projects/second-sandbox-463119-k3/topics/gmail-events`

## 🔐 **Authentication**

### **Service Account Setup**

1. **Create a service account:**
```bash
gcloud iam service-accounts create gmail-webhook-sa \
  --display-name="Gmail Webhook Service Account" \
  --project=second-sandbox-463119-k3
```

2. **Grant Pub/Sub permissions:**
```bash
gcloud projects add-iam-policy-binding second-sandbox-463119-k3 \
  --member="serviceAccount:gmail-webhook-sa@second-sandbox-463119-k3.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"
```

3. **Update subscription with service account:**
```bash
gcloud pubsub subscriptions update gmail-events-sub \
  --push-auth-service-account=gmail-webhook-sa@second-sandbox-463119-k3.iam.gserviceaccount.com \
  --project=second-sandbox-463119-k3
```

## 🧪 **Testing the Setup**

### **1. Test Topic Creation**
```bash
# List topics
gcloud pubsub topics list --project=second-sandbox-463119-k3

# Should show: gmail-events
```

### **2. Test Subscription**
```bash
# List subscriptions
gcloud pubsub subscriptions list --project=second-sandbox-463119-k3

# Should show: gmail-events-sub
```

### **3. Test Message Publishing**
```bash
# Send a test message with headers
curl -X POST https://your-domain.com/webhook/gmail \
  -H "X-Goog-Channel-Token: test@gmail.com" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

## 📊 **Monitoring**

### **Check Subscription Status**
```bash
# View subscription details
gcloud pubsub subscriptions describe gmail-events-sub \
  --project=second-sandbox-463119-k3
```

### **View Push Endpoint Logs**
```bash
# Check if messages are being delivered
gcloud pubsub subscriptions describe gmail-events-sub \
  --format="value(pushConfig.pushEndpoint)" \
  --project=second-sandbox-463119-k3
```

## 🔄 **Gmail Watch Flow**

1. **User connects Gmail** → OAuth flow completes
2. **Setup Gmail Watch** → Calls `setup_gmail_watch()` (no custom headers - Python client limitation)
3. **Gmail sends notifications** → To Pub/Sub topic
4. **Pub/Sub forwards** → To your webhook endpoint
5. **Webhook processes** → Logs all headers for debugging, processes emails

## 🎯 **Expected Headers & Payload**

**Gmail sends to Pub/Sub:**
```
Headers: (Gmail doesn't send X-Goog-Channel-Token by default)
Body: {
  "historyId": "104891",
  "emailAddress": "user@gmail.com"
}
```

**Your webhook receives:**
```
Headers: (All headers from Pub/Sub)
Body: {
  "historyId": "104891",
  "emailAddress": "user@gmail.com"
}
```

## ✅ **Success Indicators**

- ✅ Gmail Watch setup returns: `{'historyId': '104891', 'expiration': '1751115862727'}`
- ✅ Pub/Sub topic exists: `gmail-events`
- ✅ Subscription exists: `gmail-events-sub`
- ✅ Webhook endpoint responds: `{"status": "success", "processed": 1}`
- ✅ Webhook logs all headers for debugging

## 🚨 **Troubleshooting**

### **Issue: 400 Missing X-Goog-Channel-Token**
- Gmail doesn't send X-Goog-Channel-Token by default
- Check webhook logs for all headers to see what Gmail actually sends
- Consider using emailAddress from JSON body instead

### **Issue: 404 User not found**
- Check user email exists in database
- Verify email matches between Gmail and your user record
- Check webhook logs for actual email being sent

### **Issue: No messages received**
- Check Gmail Watch is active
- Verify topic and subscription exist
- Check webhook endpoint is accessible
- Review webhook logs for incoming headers

## 🔧 **Key Changes Made**

1. **Removed custom headers:** Python Gmail client doesn't support them
2. **Enhanced webhook logging:** Logs all headers for debugging
3. **Simplified watch setup:** Uses standard Gmail watch without custom headers
4. **Better error handling:** JSONResponse with proper status codes

## 📝 **Important Notes**

- **Python Gmail client limitation:** Cannot add custom headers to watch requests
- **Gmail default behavior:** Sends emailAddress in JSON body, not headers
- **Debugging approach:** Log all headers to see what Gmail actually sends
- **Alternative:** Consider using emailAddress from JSON body instead of headers

**Your Gmail webhook is now properly configured with enhanced debugging!** 🎉 