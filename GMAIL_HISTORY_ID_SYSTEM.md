# Gmail HistoryId System Implementation

## 🎯 **Overview**

This document explains the implementation of Gmail's historyId system for efficient incremental email processing. The system tracks the last processed historyId for each user and only fetches new emails since that point, avoiding duplicate processing and improving performance.

## 🔧 **How Gmail HistoryId Works**

### **What is HistoryId?**
- **HistoryId** is a Gmail API concept that represents a point in time in a user's Gmail history
- Each email operation (send, receive, delete, etc.) increments the historyId
- Gmail provides historyId in webhook notifications and API responses
- You can use historyId to fetch only changes since a specific point

### **Benefits of Using HistoryId**
1. **Efficiency**: Only fetch new emails, not all emails
2. **No Duplicates**: Avoid processing the same email multiple times
3. **Real-time**: Process emails as they arrive via webhooks
4. **Scalability**: Works efficiently even with large email volumes

## 🏗️ **System Architecture**

### **Database Schema**
```javascript
// Users collection
{
  "clerk_user_id": "user_123",
  "email": "user@gmail.com",
  "is_gmail_connected": true,
  "last_history_id": "104891",  // ← Tracked historyId
  "gmail_connected_at": "2024-01-01T00:00:00Z"
}

// Emails collection
{
  "user_id": "user_123",
  "gmail_id": "msg_456",
  "history_id": "104892",  // ← Email's historyId
  "subject": "Test Email",
  "category": "Work",
  // ... other email fields
}
```

### **Key Components**

1. **Database Functions** (`app/db/base.py`)
   - `get_user_history_id()`: Retrieve user's last processed historyId
   - `set_user_history_id()`: Update user's last processed historyId

2. **Gmail Client** (`app/services/gmail_client.py`)
   - `get_incremental_emails()`: Fetch emails since last historyId
   - `get_current_history_id()`: Get current historyId from Gmail API
   - `handle_history_id_too_old()`: Handle when historyId is too old

3. **Webhook Handler** (`app/routers/webhook.py`)
   - Extracts historyId from webhook payload
   - Uses incremental sync when possible
   - Falls back to full sync when needed

## 🔄 **Workflow**

### **1. Initial Setup**
```python
# When user connects Gmail
async def setup_gmail_watch(user_id: str):
    # Set up Gmail push notifications
    response = service.users().watch(userId="me", body=watch_request).execute()
    
    # Store initial historyId
    history_id = response.get("historyId")
    await set_user_history_id(user_id, history_id)
```

### **2. Webhook Processing**
```python
# When Gmail sends webhook
async def gmail_push_webhook(request: Request):
    # Extract historyId from webhook
    webhook_data = decode_webhook_payload(request)
    webhook_history_id = webhook_data.get("historyId")
    
    # Get user's last processed historyId
    last_history_id = await get_user_history_id(user_id)
    
    if webhook_history_id and last_history_id:
        # Use incremental sync
        emails = await get_incremental_emails(user_id, last_history_id)
        await set_user_history_id(user_id, webhook_history_id)
    else:
        # Fallback to full sync
        emails = await fetch_and_process_new_emails(user_id)
```

### **3. Incremental Email Fetching**
```python
async def get_incremental_emails(user_id: str, last_history_id: str):
    # Fetch history since last_history_id
    history = service.users().history().list(
        userId='me',
        startHistoryId=last_history_id,
        historyTypes=['messageAdded']
    ).execute()
    
    # Process only new messages
    for record in history.get('history', []):
        for msg in record.get('messagesAdded', []):
            # Process and save email
            await process_and_save_email(msg['message'])
```

## 🛠️ **Implementation Details**

### **HistoryId Storage**
```python
# Store historyId per user
async def set_user_history_id(clerk_user_id: str, history_id: str):
    await db.get_collection('users').update_one(
        {"clerk_user_id": clerk_user_id},
        {"$set": {"last_history_id": history_id}}
    )

# Retrieve historyId for user
async def get_user_history_id(clerk_user_id: str) -> str:
    user = await db.get_collection('users').find_one({"clerk_user_id": clerk_user_id})
    return user.get("last_history_id") if user else None
```

### **Incremental Email Processing**
```python
async def get_incremental_emails(user_id: str, last_history_id: str) -> List[Dict]:
    try:
        service = await get_gmail_service_for_user(user_id)
        
        # Fetch history since last_history_id
        history = service.users().history().list(
            userId='me',
            startHistoryId=last_history_id,
            historyTypes=['messageAdded']
        ).execute()
        
        # Check if historyId is too old
        if 'historyId' in history:
            logger.warning(f"HistoryId {last_history_id} is too old")
            return []
        
        # Process new messages
        messages = []
        for record in history.get('history', []):
            for msg in record.get('messagesAdded', []):
                messages.append(msg['message'])
        
        # Process each message
        processed_emails = []
        for message in messages:
            email_data = await process_gmail_message(message, user_id)
            if email_data:
                processed_emails.append(email_data)
        
        return processed_emails
        
    except Exception as e:
        logger.error(f"Error fetching incremental emails: {e}")
        return []
```

### **Handling Old HistoryId**
```python
async def handle_history_id_too_old(user_id: str, old_history_id: str):
    # Get current historyId from Gmail
    current_history_id = await get_current_history_id(user_id)
    
    # Do full sync of recent emails
    emails = await get_latest_emails(user_id, max_results=50)
    
    # Update to current historyId
    await set_user_history_id(user_id, current_history_id)
    
    return emails
```

## 🧪 **Testing**

### **Test Cases**
```python
# Test incremental email fetching
async def test_get_incremental_emails_success():
    emails = await get_incremental_emails("user123", "12344")
    assert len(emails) == 1
    assert emails[0]['history_id'] == "12346"

# Test handling old historyId
async def test_handle_history_id_too_old():
    emails = await handle_history_id_too_old("user123", "12344")
    # Should do full sync and update historyId
```

### **Running Tests**
```bash
# Run historyId system tests
pytest tests/test_gmail_history_system.py -v

# Run specific test
pytest tests/test_gmail_history_system.py::TestGmailHistorySystem::test_get_incremental_emails_success -v
```

## 📊 **Monitoring & Debugging**

### **Log Messages**
```
[Webhook] Push notification for: user@gmail.com, historyId: 104891
[Webhook] User user123 last_history_id: 104890, webhook_history_id: 104891
[Webhook] Found 3 new messages since historyId: 104890
[Webhook] Updated user user123 last_history_id to: 104891
[Webhook] 3 email(s) processed and saved for user_id=user123
```

### **Error Handling**
```python
# HistoryId too old
if 'historyId' in history:
    logger.warning(f"HistoryId {last_history_id} is too old")
    return await handle_history_id_too_old(user_id, last_history_id)

# No new messages
if not history_records:
    logger.info(f"No new messages found since historyId: {last_history_id}")
    return []
```

## 🔧 **Configuration**

### **Environment Variables**
```env
# Gmail Configuration
GOOGLE_PROJECT_ID=your-project-id
GMAIL_WEBHOOK_TOPIC=gmail-events
```

### **Database Indexes**
```python
# Ensure indexes for performance
await collection.create_index("clerk_user_id", unique=True)
await collection.create_index("gmail_id", unique=True, sparse=True)
await collection.create_index("history_id", sparse=True)
```

## 🚀 **Deployment Considerations**

### **Migration Script**
```python
# scripts/migrate_set_history_id.py
async def migrate_set_history_id():
    users = users_collection.find({"is_gmail_connected": True})
    for user in users:
        history_id = await get_current_history_id(user["clerk_user_id"])
        if history_id:
            await set_user_history_id(user["clerk_user_id"], history_id)
```

### **Health Checks**
```python
async def check_history_id_system():
    # Check if historyId is being tracked properly
    users_with_gmail = await count_users_with_gmail()
    users_with_history_id = await count_users_with_history_id()
    
    return {
        "gmail_users": users_with_gmail,
        "users_with_history_id": users_with_history_id,
        "coverage": users_with_history_id / users_with_gmail if users_with_gmail > 0 else 0
    }
```

## 📈 **Performance Benefits**

### **Before HistoryId System**
- ❌ Fetch all unread emails on every webhook
- ❌ Process duplicate emails
- ❌ High API quota usage
- ❌ Slow processing times

### **After HistoryId System**
- ✅ Only fetch new emails since last webhook
- ✅ No duplicate processing
- ✅ Minimal API quota usage
- ✅ Fast incremental processing

## 🔍 **Troubleshooting**

### **Common Issues**

1. **HistoryId Too Old**
   ```
   Solution: Use handle_history_id_too_old() to do full sync
   ```

2. **No Emails Processed**
   ```
   Check: Webhook payload contains historyId
   Check: User has valid last_history_id in database
   ```

3. **Duplicate Emails**
   ```
   Check: gmail_id unique index is working
   Check: already_classified() function is called
   ```

### **Debug Commands**
```python
# Check user's historyId
history_id = await get_user_history_id("user123")
print(f"User historyId: {history_id}")

# Get current Gmail historyId
current_id = await get_current_history_id("user123")
print(f"Current Gmail historyId: {current_id}")

# Test incremental sync
emails = await get_incremental_emails("user123", history_id)
print(f"Found {len(emails)} new emails")
```

## ✅ **Success Indicators**

- ✅ Webhook logs show historyId progression
- ✅ No duplicate emails in database
- ✅ Fast webhook response times
- ✅ Low Gmail API quota usage
- ✅ All users have last_history_id set

---

**The Gmail HistoryId system is now properly implemented for efficient incremental email processing!** 🎉 