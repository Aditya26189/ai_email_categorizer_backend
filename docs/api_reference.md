# API Reference

All endpoints require Clerk authentication via Bearer token in the Authorization header unless otherwise noted:

```
Authorization: Bearer <clerk_token>
```

---

## User Management

### GET /routers/v1/me
Get current user profile with Gmail connection status.

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

## Gmail OAuth Integration

### GET /routers/v1/gmail/oauth-url
Generate OAuth URL for Gmail integration.

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?...",
  "state": "random_state_string",
  "user_id": "user_2xYk123"
}
```

### POST /routers/v1/gmail/callback
Exchange authorization code for tokens.

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

### GET /routers/v1/gmail/oauth/status
Check Gmail connection status.

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
Remove Gmail connection.

**Response:**
```json
{
  "success": true,
  "message": "Gmail disconnected successfully"
}
```

---

## Email Management

### GET /routers/v1/emails/emails
Get user's emails with filtering and pagination.

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
Get emails grouped by category.

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
      "category": "Work"
    }
  ],
  "Personal": [
    // ... personal emails
  ]
}
```

### GET /routers/v1/emails/categories
Get all available email categories.

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

## Email Classification

### POST /routers/v1/classify/
Classify and store a single email.

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
  "gmail_id": "gmail_message_id",
  "category": "Work",
  "summary": ["Point 1", "Point 2"],
  "status": "classified"
}
```

---

## Gmail Webhook

### POST /webhook/gmail
Receives Gmail push notifications (Google Pub/Sub). No authentication required (Google signed).

**Request Body Example:**
```json
{
  "historyId": "104891",
  "emailAddress": "user@gmail.com"
}
```
**Response Example:**
```json
{
  "status": "success",
  "processed": 1
}
```

---

## OAuth Endpoints (Summary)
- `GET /gmail/oauth/url` - Generate OAuth authorization URL
- `GET /gmail/oauth/callback` - Handle OAuth callback
- `GET /gmail/oauth/status` - Check OAuth connection status
- `DELETE /gmail/oauth/revoke` - Revoke OAuth access
- `POST /gmail/watch/setup` - Set up Gmail push notifications

---

## Headers & Tokens
- All endpoints (except webhook) require:
  - `Authorization: Bearer <clerk_token>`
- Content-Type: `application/json` for POST/PUT

---

## Error Responses
All errors return a JSON object with a `detail` field:
```json
{
  "detail": "Error message here."
}
``` 