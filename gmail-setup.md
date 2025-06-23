# GMAIL SETUP

## Gmail pub/sub - method to fetch the mails instantly

---

## 🔜 **Your Manual Next Steps**

### 🔐 1. **Set Up Gmail Pub/Sub Push Notifications**

You’ll need:

- A verified Google Cloud project
- OAuth 2.0 credentials
- Gmail API and Pub/Sub API enabled

**Steps:**

1. **Create a Pub/Sub topic** in GCP console
    
    Example: `projects/YOUR_PROJECT/topics/gmail-events`
    
2. **Create a subscription** to that topic (type = *Push*)
    
    Set **push endpoint** as:
    
    ```
    https://your-domain.com/webhook/gmail
    
    ```
    
3. **Grant Gmail permissions to publish to the topic**
    
    Add this member:
    
    ```
    gmail-api-push@system.gserviceaccount.com
    
    ```
    
    With **Pub/Sub Publisher** role
    

---

### ⚙️ 2. **Call Gmail `watch` API**

Use the `users.watch` endpoint to register Gmail watch:

**POST https://gmail.googleapis.com/gmail/v1/users/me/watch**

**Request Body:**

```json
{
  "labelIds": ["INBOX"],
  "topicName": "projects/YOUR_PROJECT/topics/gmail-events"
}

```

Use the authenticated Gmail API client for each user to call this.

This will:

- Register Gmail to send notifications to your Pub/Sub topic
- Trigger your `/webhook/gmail` on new mail

---

### 🔍 3. **Verify the End-to-End Flow**

1. Send a test email to your Gmail.
2. Check logs:
    - Gmail → Pub/Sub → `/webhook/gmail`
    - Webhook calls `fetch_and_process_new_emails(user_id)`
    - Email gets inserted into MongoDB **after** AI processing
3. See frontend update via polling (WebSocket removed).

---

## 🛡️ Optional Enhancements

- 🔑 **Add webhook authentication**: Use HMAC or bearer token to protect the webhook
- 📦 **Log email fetch outcomes**: Store in logs or DB to debug retries/errors
- 📅 **Auto-renew `watch`** every 7 days (Gmail watches expire)

---

If you want, I can:

- Generate `watch_gmail.py` to automate the `users.watch` call
- Help with setting up OAuth credentials for Gmail API
- Add webhook verification/auth logic

Just say the word!

## pub/sub credentials

Subscription name: projects/second-sandbox-463119-k3/subscriptions/tidymail

topics - gmail-events

link for service account → [Service accounts – IAM & Admin – Email AI Auth – Google Cloud console](https://console.cloud.google.com/iam-admin/serviceaccounts?authuser=1&inv=1&invt=Ab0o5A&project=second-sandbox-463119-k3&supportedpurview=project)

link for pub/sub → [gmail-events – Pub/Sub – Email AI Auth – Google Cloud console](https://console.cloud.google.com/cloudpubsub/subscription/detail/gmail-events?authuser=1&inv=1&invt=Ab0o6A&project=second-sandbox-463119-k3&tab=overview) 

## How to grant access to pub/sub

Great — it looks like you're in the **Pub/Sub Topic Permissions** page for your topic `gmail-events`.

To **confirm and finish the setup**, follow these final checks:

---

## ✅ Step-by-Step Final Confirmation

### ✅ 1. **Pub/Sub Publisher Role**

Make sure this line is present:

- **Role:** `Pub/Sub Publisher`
- **Principal:** `gmail-api-push@system.gserviceaccount.com`

🔍 If you **don’t see this exact principal**, do this:

### ➕ Add Gmail API Push as Publisher:

1. Click **"Add principal"**
2. In **New principal**, paste:
    
    ```
    gmail-api-push@system.gserviceaccount.com
    
    ```
    
3. Under **Roles**, search and select:
    
    ```
    Pub/Sub Publisher
    
    ```
    
4. (Optional but good): Click **“Add condition”** and add:
    
    ```
    resource.name.startsWith("projects/YOUR_PROJECT_ID/topics/gmail-events")
    
    ```
    
5. Click **Save**

---

### ✅ 2. **Pub/Sub Subscriber Role**

This should be assigned to **your backend service account** that listens to the messages. You should see:

- **Role:** `Pub/Sub Subscriber`
- **Principal:** Your app’s service account (e.g. `tidymail-api@your-project.iam.gserviceaccount.com`)

---

### ✅ 3. **Owner**

That’s fine to be you or your organization for full access. No action needed here.

---

## ✅ Now What?

Once `gmail-api-push@system.gserviceaccount.com` has **Pub/Sub Publisher** access to the topic:

- You can now **call the Gmail `watch` API** from your backend or scripts
- New emails will trigger **push events to the topic**
- Your webhook (via your FastAPI `/webhook/gmail` route) will be invoked
- Your `fetch_and_process_new_emails()` function will summarize and insert emails into MongoDB
- Your frontend will see the data

---

If you're ready, I can help you call the **Gmail `watch` API** next — or verify the whole webhook trigger. Let me know!