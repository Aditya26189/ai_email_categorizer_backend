# Frontend OAuth Implementation Checklist

## 🔐 Security Requirements (CRITICAL)

### ✅ State Parameter Validation
- [ ] Backend generates random `state` in `/gmail/oauth/start`
- [ ] Frontend stores `state` in localStorage/sessionStorage
- [ ] Frontend compares URL `state` with stored `state` in callback
- [ ] Frontend rejects callback if states don't match
- [ ] Frontend clears stored `state` after validation

### ✅ CSRF Protection
- [ ] State validation prevents cross-site request forgery
- [ ] OAuth callback only proceeds with valid state
- [ ] Error handling for invalid states

## 🔄 OAuth Flow Implementation

### Step 1: Start OAuth Flow
```typescript
// ✅ Correct Implementation
const startGmailOAuth = async () => {
  try {
    const response = await fetch('/routers/v1/gmail/oauth/start', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const { auth_url, state, user_id } = await response.json();
    
    // Store state securely
    localStorage.setItem('gmail_oauth_state', state);
    
    // Redirect to Google
    window.location.href = auth_url;
  } catch (error) {
    console.error('Failed to start OAuth:', error);
  }
};
```

### Step 2: Handle OAuth Callback
```typescript
// ✅ Correct Implementation
const handleOAuthCallback = async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  const state = urlParams.get('state');
  const storedState = localStorage.getItem('gmail_oauth_state');
  
  // Validate state
  if (!state || state !== storedState) {
    console.error('Invalid OAuth state - possible CSRF attack');
    // Show error to user
    return;
  }
  
  // Clear stored state
  localStorage.removeItem('gmail_oauth_state');
  
  try {
    // Complete OAuth with backend
    const response = await fetch('/routers/v1/gmail/callback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ code, state })
    });
    
    if (response.ok) {
      // Refresh user profile/status
      await refreshUserProfile();
      // Update UI to hide connect popup
    }
  } catch (error) {
    console.error('OAuth callback failed:', error);
  }
};
```

### Step 3: Post-OAuth Success
```typescript
// ✅ Correct Implementation
const refreshUserProfile = async () => {
  try {
    // Get updated user profile with Gmail status
    const response = await fetch('/routers/v1/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const user = await response.json();
    
    // Update UI based on Gmail connection status
    if (user.is_gmail_connected) {
      // Hide connect popup, show connected status
      setGmailConnected(true);
    }
  } catch (error) {
    console.error('Failed to refresh user profile:', error);
  }
};
```

## 🚨 Common Issues & Solutions

### Issue 1: CSRF Warning Still Appears
**Cause:** State validation not working properly
**Solution:** 
- Check that `state` is being stored and retrieved correctly
- Verify state comparison logic
- Add debug logging

### Issue 2: Gmail Connect Popup Reappears
**Cause:** User profile not refreshed after OAuth success
**Solution:**
- Call `/me` endpoint after successful OAuth
- Update UI state based on `is_gmail_connected` field
- Clear any cached user data

### Issue 3: OAuth Callback Fails
**Cause:** Backend validation issues
**Solution:**
- Check that both `code` and `state` are sent to backend
- Verify Authorization header is present
- Check backend logs for specific errors

## 🔍 Debug Checklist

### Add Debug Logging
```typescript
// Add these logs to debug OAuth flow
console.log('OAuth Start - State:', state);
console.log('OAuth Callback - URL State:', urlState);
console.log('OAuth Callback - Stored State:', storedState);
console.log('OAuth Callback - States Match:', urlState === storedState);
```

### Test Scenarios
- [ ] Fresh OAuth flow (no existing state)
- [ ] OAuth flow with existing Gmail connection
- [ ] OAuth callback with invalid state
- [ ] OAuth callback with missing state
- [ ] Network error during OAuth start
- [ ] Network error during OAuth callback

## 📱 UI/UX Requirements

### Loading States
- [ ] Show loading spinner during OAuth start
- [ ] Show loading spinner during OAuth callback
- [ ] Disable buttons during OAuth flow

### Error Handling
- [ ] Show user-friendly error messages
- [ ] Provide retry options for failed OAuth
- [ ] Handle network errors gracefully

### Success Feedback
- [ ] Show success message after OAuth completion
- [ ] Update UI to reflect Gmail connection
- [ ] Hide connect popup after success

## 🧪 Testing Checklist

### Manual Testing
- [ ] Complete OAuth flow end-to-end
- [ ] Test with different browsers
- [ ] Test with incognito/private mode
- [ ] Test with network interruptions
- [ ] Test with invalid states

### Security Testing
- [ ] Verify CSRF protection works
- [ ] Test with tampered state parameter
- [ ] Verify state cleanup after use

## 📋 Backend Integration Points

### Required Endpoints
- [ ] `GET /routers/v1/gmail/oauth/start` - Start OAuth flow
- [ ] `POST /routers/v1/gmail/callback` - Complete OAuth
- [ ] `GET /routers/v1/me` - Get user profile with Gmail status
- [ ] `GET /routers/v1/gmail/oauth/status` - Check Gmail connection

### Expected Response Formats
```typescript
// OAuth Start Response
{
  auth_url: string;
  state: string;
  user_id: string;
}

// OAuth Callback Response
{
  success: boolean;
  message: string;
}

// User Profile Response
{
  clerk_user_id: string;
  email: string;
  is_gmail_connected: boolean;
  gmail_email: string;
  gmail_connected_at: string;
}
```

## 🎯 Success Criteria

Your OAuth implementation is successful when:
- [ ] No CSRF warnings appear
- [ ] Gmail connect popup only shows when Gmail is not connected
- [ ] OAuth flow completes successfully
- [ ] User profile updates correctly after OAuth
- [ ] UI reflects the correct Gmail connection status
- [ ] Error handling works for all failure scenarios 