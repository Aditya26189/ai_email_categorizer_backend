 # API Endpoints Documentation

## 🔐 Authentication
All endpoints require Clerk authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <clerk_token>
```

---

## 👤 User Management

### GET /routers/v1/me
**Get current user profile with Gmail connection status**

**Response:**
```json
{
  "clerk_user_id": "user_2xYk123",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "image_url": "https://...",
  "username": "johndoe",
  "is_gmail_connected": true,
  "gmail_email": "user@gmail.com",
  "gmail_connected_at": "2025-06-21T10:00:00Z",
  "updated_at": "2025-06-21T10:00:00Z",
  "created_at": "2025-06-21T10:00:00Z"
}
```

---

## 📧 Gmail OAuth Integration

### GET /routers/v1/gmail/oauth-url
**Generate OAuth URL for Gmail integration**

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?client_id=...&redirect_uri=...&scope=...&response_type=code&access_type=offline&prompt=consent&include_granted_scopes=true&state=...",
  "state": "random_state_string",
  "user_id": "user_2xYk123"
}
```

### POST /routers/v1/gmail/callback
**Exchange authorization code for tokens (API call)**

**Request Body:**
```json
{
  "code": "AUTHORIZATION_CODE_FROM_GOOGLE",
  "state": "STATE_STRING_FOR_VERIFICATION"
}
```

**Response:**
```json
{
  "success": true,
  "oauth_result": {
    "success": true,
    "user_id": "user_2xYk123",
    "email": "user@gmail.com",
    "name": "User Name",
    "scopes": ["openid", "email", "profile", ...],
    "is_gmail_connected": true
  },
  "gmail_watch_setup": true,
  "message": "Gmail integration completed successfully"
}
```

### GET /routers/v1/gmail/status
**Check Gmail connection status**

**Response:**
```json
{
  "is_gmail_connected": true,
  "user_id": "user_2xYk123",
  "email": "user@example.com",
  "gmail_email": "user@gmail.com",
  "gmail_connected_at": "2025-06-21T10:00:00Z",
  "message": "Gmail connected"
}
```

### DELETE /routers/v1/gmail/disconnect
**Remove Gmail connection**

**Response:**
```json
{
  "success": true,
  "message": "Gmail disconnected successfully"
}
```

---

## 📧 Email Management

### GET /routers/v1/emails/emails
**Get user's emails with filtering and pagination**

**Query Parameters:**
- `category` (optional): Filter by category
- `page` (default: 1): Page number
- `limit` (default: 20, max: 100): Items per page
- `q` (optional): Search query (2-100 chars)

**Response:**
```json
[
  {
    "user_id": "user_2xYk123",
    "gmail_id": "gmail_message_id",
    "subject": "Email Subject",
    "body": "Email body content...",
    "category": "Work",
    "summary": ["Point 1", "Point 2"],
    "sender_name": "Sender Name",
    "sender_email": "sender@example.com",
    "timestamp": "2025-06-21T10:00:00Z",
    "is_read": false,
    "is_processed": true,
    "status": "new"
  }
]
```

### GET /routers/v1/emails/by-categories
**Get emails grouped by category**

**Query Parameters:**
- `page` (default: 1): Page number
- `limit` (default: 20, max: 100): Items per page per category
- `q` (optional): Search query (2-100 chars)

**Response:**
```json
{
  "Work": [
    {
      "user_id": "user_2xYk123",
      "gmail_id": "gmail_message_id",
      "subject": "Work Email",
      "category": "Work",
      // ... other email fields
    }
  ],
  "Personal": [
    // ... personal emails
  ]
}
```

### GET /routers/v1/emails/categories
**Get all available email categories**

**Response:**
```json
[
  "Important",
  "Work", 
  "Personal",
  "Finance",
  "Travel",
  "Shopping",
  "Entertainment",
  "Health",
  "Education",
  "Other"
]
```

---

## 🤖 Email Classification

### POST /routers/v1/classify/
**Classify and store a single email**

**Request Body:**
```json
{
  "gmail_id": "gmail_message_id",
  "subject": "Email Subject",
  "body": "Email body content...",
  "sender_name": "Sender Name",
  "sender_email": "sender@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "email": {
    "user_id": "user_2xYk123",
    "gmail_id": "gmail_message_id",
    "subject": "Email Subject",
    "category": "Work",
    "summary": ["Point 1", "Point 2"],
    "sender_name": "Sender Name",
    "sender_email": "sender@example.com",
    "timestamp": "2025-06-21T10:00:00Z"
  }
}
```

### GET /routers/v1/classify/emails
**Fetch and process latest emails from Gmail**

**Query Parameters:**
- `batch_size` (default: 10, max: 50): Number of emails to process

**Response:**
```json
[
  {
    "gmail_id": "gmail_message_id",
    "subject": "Email Subject",
    "body": "Email body content...",
    "sender_name": "Sender Name",
    "sender_email": "sender@example.com",
    "timestamp": "2025-06-21T10:00:00Z"
  }
]
```

---

## 🔄 Gmail Watch & Webhooks

### POST /routers/v1/gmail/watch/setup
**Set up Gmail push notifications**

**Response:**
```json
{
  "success": true,
  "message": "Gmail push notifications set up successfully"
}
```

### POST /webhook/gmail
**Receive Gmail push notifications (no auth required)**

**Request Body:**
```json
{
  "user_id": "user_2xYk123"
}
```

**Response:**
```json
{
  "status": "success",
  "processed": 5
}
```

---

## 🏥 Health Check

### GET /routers/v1/health
**Comprehensive health check for all services**

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-21T10:00:00Z",
  "services": {
    "mongodb": {
      "status": "healthy",
      "details": {
        "connection": "connected",
        "database": "email_categorizer",
        "collections": 3,
        "documents": 150,
        "data_size": "2.45 MB",
        "storage_size": "3.12 MB"
      }
    },
    "gmail_api": {
      "status": "healthy",
      "details": {
        "connection": "configured",
        "oauth_configured": true,
        "client_id": "1234567890..."
      }
    },
    "llm_service": {
      "status": "healthy",
      "details": {
        "connection": "connected",
        "response_time": "0.15s",
        "api_url": "https://generativelanguage.googleapis.com"
      }
    }
  }
}
```

---

## 📝 Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (invalid/missing token)
- `404`: Not Found (resource doesn't exist)
- `409`: Conflict (e.g., email already exists)
- `500`: Internal Server Error

---

## 🔗 Frontend Integration Examples

### Check Gmail Status
```typescript
const checkGmailStatus = async () => {
  const response = await fetch('/routers/v1/gmail/status', {
    headers: { 'Authorization': `Bearer ${clerkToken}` }
  });
  return response.json();
};
```

### Start OAuth Flow
```typescript
const startOAuth = async () => {
  const response = await fetch('/routers/v1/gmail/oauth-url', {
    headers: { 'Authorization': `Bearer ${clerkToken}` }
  });
  const { auth_url } = await response.json();
  window.location.href = auth_url;
};
```

### Complete OAuth Callback
```typescript
const completeOAuth = async (code: string, state: string) => {
  const response = await fetch('/routers/v1/gmail/callback', {
    method: 'POST',
    headers: { 
      'Authorization': `Bearer ${clerkToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ code, state })
  });
  return response.json();
};
```

### Get User Profile
```typescript
const getUserProfile = async () => {
  const response = await fetch('/routers/v1/me', {
    headers: { 'Authorization': `Bearer ${clerkToken}` }
  });
  return response.json();
};
```
