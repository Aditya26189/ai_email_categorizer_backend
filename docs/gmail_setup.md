# Gmail Setup Guide

This guide explains how to configure Gmail API, OAuth, and Pub/Sub for TidyMail, and what is needed for production re-approval.

---

## 1. Gmail OAuth Scopes

### Non-sensitive
- `openid`, `email`, `profile`: Basic user info
- `https://www.googleapis.com/auth/gmail.readonly`: Read emails

### Sensitive
- `https://www.googleapis.com/auth/gmail.modify`: Read, mark as read, move, or delete emails
- `https://www.googleapis.com/auth/gmail.send`: Send emails
- `https://www.googleapis.com/auth/gmail.labels`: Manage labels
- `https://www.googleapis.com/auth/gmail.settings.basic`: Read basic settings

### Restricted
- None by default (avoid unless absolutely needed)

**What each enables:**
- `readonly`: Fetch and display emails
- `modify`: Mark as read, archive, delete
- `send`: Send emails on user's behalf
- `labels`: Categorize and organize emails
- `settings.basic`: Read settings for advanced features

---

## 2. OAuth Client Details
- **Google Cloud Project:** `second-sandbox-463119-k3` (example)
- **OAuth Client Type:** Web application
- **Redirect URI:** `http://localhost:8000/gmail/oauth/callback` (dev), your deployed backend in prod
- **Client ID/Secret:** In Google Cloud Console > APIs & Services > Credentials

---

## 3. Pub/Sub Setup

### a. Create Topic
```bash
gcloud pubsub topics create gmail-events --project=second-sandbox-463119-k3
```

### b. Create Push Subscription
```bash
gcloud pubsub subscriptions create gmail-events-sub \
  --topic=gmail-events \
  --push-endpoint=https://your-domain.com/webhook/gmail \
  --project=second-sandbox-463119-k3
```

### c. For Local Development (ngrok)
```bash
ngrok http 8000
# Update subscription with ngrok URL
gcloud pubsub subscriptions update gmail-events-sub \
  --push-endpoint=https://your-ngrok-url.ngrok.io/webhook/gmail \
  --project=second-sandbox-463119-k3
```

---

## 4. Service Account for Pub/Sub
- **Create:**
```bash
gcloud iam service-accounts create gmail-webhook-sa \
  --display-name="Gmail Webhook Service Account" \
  --project=second-sandbox-463119-k3
```
- **Grant Pub/Sub permissions:**
```bash
gcloud projects add-iam-policy-binding second-sandbox-463119-k3 \
  --member="serviceAccount:gmail-webhook-sa@second-sandbox-463119-k3.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"
```
- **Update subscription to use service account:**
```bash
gcloud pubsub subscriptions update gmail-events-sub \
  --push-auth-service-account=gmail-webhook-sa@second-sandbox-463119-k3.iam.gserviceaccount.com \
  --project=second-sandbox-463119-k3
```

---

## 5. Reapplying for Production (Google Verification)
If you need to reapply for production (restricted/sensitive scopes):
- **Privacy Policy:** Publicly accessible, clear about data use
- **Use Case Description:** Why you need each scope
- **Limited-Use Justification:** Explain why you need sensitive scopes
- **Demo Video:** Show the full OAuth flow, what data is accessed, and how it's used
- **OAuth Consent Screen:** Fill out all required fields in Google Cloud Console
- **Contact Info:** Valid support email

---

## 6. Links
- [Google Cloud Credentials](https://console.cloud.google.com/apis/credentials?project=second-sandbox-463119-k3)
- [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts?project=second-sandbox-463119-k3)
- [Pub/Sub Topics](https://console.cloud.google.com/cloudpubsub/topic/list?project=second-sandbox-463119-k3)

---

## 7. Troubleshooting
- 403 errors: Check Clerk JWT, OAuth scopes, and Pub/Sub permissions
- Webhook not firing: Check Pub/Sub push endpoint and ngrok URL
- See `GMAIL_WEBHOOK_SETUP.md` for more debugging tips 