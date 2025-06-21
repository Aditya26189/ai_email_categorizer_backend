# Gmail Endpoints Guide & 403 Error Fix

## 🚨 **403 Error on `/routers/v1/gmail/watch/setup`**

The 403 error indicates an **authentication failure**. Here's how to fix it:

## 🔐 **Authentication Requirements**

All Gmail endpoints require a valid **Clerk JWT token** in the Authorization header:

```http
Authorization: Bearer <your_clerk_jwt_token>
```

## 📋 **Available Gmail Endpoints**

### **✅ Working Endpoints**
```
GET  /routers/v1/gmail/oauth/status     - Check Gmail connection status
GET  /routers/v1/gmail/oauth/start      - Start OAuth flow
GET  /routers/v1/gmail/oauth/url        - Generate OAuth URL
POST /routers/v1/gmail/callback         - Complete OAuth
DELETE /routers/v1/gmail/oauth/revoke   - Revoke OAuth access
DELETE /routers/v1/gmail/disconnect     - Disconnect Gmail
POST /routers/v1/gmail/watch/setup      - Set up Gmail push notifications
```

### **❌ Common Wrong Endpoints**
```
GET  /routers/v1/gmail/status           ❌ Wrong (missing /oauth/)
GET  /routers/v1/gmail/status           ❌ Wrong (extra spaces)
```

## 🔧 **How to Fix the 403 Error**

### **1. Check Your Authorization Header**

**Frontend (JavaScript/TypeScript):**
```typescript
const response = await fetch('/routers/v1/gmail/watch/setup', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${clerkToken}`,  // Make sure this is present
    'Content-Type': 'application/json'
  }
});
```

**cURL/Postman:**
```bash
curl -X POST "http://localhost:8000/routers/v1/gmail/watch/setup" \
  -H "Authorization: Bearer YOUR_CLERK_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### **2. Verify Your Clerk Token**

**Check if token is valid:**
```typescript
// In your frontend, verify the token before making requests
if (!clerkToken) {
  console.error('No Clerk token available');
  return;
}

console.log('Token exists:', !!clerkToken);
console.log('Token length:', clerkToken.length);
```

### **3. Test Authentication First**

**Test with a simple endpoint:**
```typescript
// Test authentication with /me endpoint first
const meResponse = await fetch('/routers/v1/me', {
  headers: {
    'Authorization': `Bearer ${clerkToken}`
  }
});

if (meResponse.status === 200) {
  console.log('✅ Authentication working');
  // Now try the Gmail endpoint
} else {
  console.error('❌ Authentication failed:', meResponse.status);
}
```

## 🧪 **Debugging Steps**

### **Step 1: Check Server Logs**
Look for authentication errors in your server logs:
```
❌ JWT validation failed: ...
❌ No Clerk user ID (sub) in JWT
❌ Invalid Authentication Credentials
```

### **Step 2: Test Token Validity**
```typescript
// Add this to your frontend to debug
const testAuth = async () => {
  try {
    const response = await fetch('/routers/v1/me', {
      headers: {
        'Authorization': `Bearer ${clerkToken}`
      }
    });
    
    console.log('Auth test status:', response.status);
    if (response.ok) {
      const user = await response.json();
      console.log('User authenticated:', user.clerk_user_id);
    } else {
      console.error('Auth failed:', response.statusText);
    }
  } catch (error) {
    console.error('Auth test error:', error);
  }
};
```

### **Step 3: Check Gmail Connection Status**
Before calling `/watch/setup`, check if Gmail is connected:
```typescript
const checkGmailStatus = async () => {
  const response = await fetch('/routers/v1/gmail/oauth/status', {
    headers: {
      'Authorization': `Bearer ${clerkToken}`
    }
  });
  
  if (response.ok) {
    const status = await response.json();
    console.log('Gmail status:', status);
    
    if (status.is_connected) {
      // Now try watch setup
      await setupGmailWatch();
    } else {
      console.log('Gmail not connected yet');
    }
  }
};
```

## 🎯 **Complete Working Example**

```typescript
const setupGmailWatch = async () => {
  try {
    // 1. Check authentication
    const meResponse = await fetch('/routers/v1/me', {
      headers: {
        'Authorization': `Bearer ${clerkToken}`
      }
    });
    
    if (meResponse.status !== 200) {
      console.error('❌ Authentication failed');
      return;
    }
    
    // 2. Check Gmail connection
    const statusResponse = await fetch('/routers/v1/gmail/oauth/status', {
      headers: {
        'Authorization': `Bearer ${clerkToken}`
      }
    });
    
    if (statusResponse.ok) {
      const status = await statusResponse.json();
      
      if (!status.is_connected) {
        console.log('❌ Gmail not connected');
        return;
      }
    }
    
    // 3. Set up Gmail watch
    const watchResponse = await fetch('/routers/v1/gmail/watch/setup', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${clerkToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (watchResponse.ok) {
      const result = await watchResponse.json();
      console.log('✅ Gmail watch setup:', result);
    } else {
      console.error('❌ Watch setup failed:', watchResponse.status);
    }
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
};
```

## 🚀 **Quick Fix Checklist**

- [ ] **Include Authorization header** with Bearer token
- [ ] **Verify Clerk token is valid** and not expired
- [ ] **Test authentication** with `/me` endpoint first
- [ ] **Check Gmail connection** with `/oauth/status` before watch setup
- [ ] **Use correct endpoint** `/routers/v1/gmail/watch/setup`
- [ ] **Check server logs** for authentication errors

## 📞 **Common Issues & Solutions**

### **Issue 1: Missing Authorization Header**
**Solution:** Add `Authorization: Bearer <token>` header

### **Issue 2: Invalid Token**
**Solution:** Get a fresh token from Clerk

### **Issue 3: Token Expired**
**Solution:** Refresh the token or re-authenticate

### **Issue 4: Gmail Not Connected**
**Solution:** Complete OAuth flow first, then try watch setup

**The 403 error should be resolved once you have a valid Clerk JWT token in the Authorization header!** 🔐 