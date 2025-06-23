# Frontend Notes

This document summarizes the current state of the TidyMail frontend, its main components, and areas for improvement.

---

## 1. What the UI Does
- Authenticates users via Clerk
- Shows Gmail Connect modal if Gmail is not connected
- Initiates and completes Gmail OAuth flow (with state validation)
- Displays categorized and summarized emails in a list
- Allows filtering by category and searching emails
- Shows email details and AI-generated summaries
- Handles loading, error, and success states for OAuth and email fetch

---

## 2. Main Pages & Components
- **GmailConnectModal**: Handles Gmail OAuth start, state storage, and callback validation
- **EmailList**: Shows all emails, grouped or filtered by category
- **EmailDetail**: Displays full email content and summary
- **UserProfile**: Shows user info and Gmail connection status
- **OAuthCallbackPage**: Handles OAuth code/state from Google, completes backend handshake
- **Loading/Error Components**: For all async actions

---

## 3. State Flow
- On login, fetch `/me` to get user and Gmail status
- If `is_gmail_connected` is false, show GmailConnectModal
- On connect, start OAuth, store state in localStorage
- On callback, validate state, POST code/state to backend
- On success, refresh user profile and hide modal
- Fetch emails from `/emails/emails` and display

---

## 4. What's Incomplete or Could Be Improved
- **UI Polish:** Some modals and error messages are basic
- **Mobile Responsiveness:** Needs more testing and tweaks
- **Bulk Actions:** No bulk archive/delete yet
- **Real-time Updates:** Polling is used; WebSocket support would be better
- **Email Compose/Reply:** Not implemented
- **Settings Page:** For user preferences, categories, etc.
- **OAuth Edge Cases:** More robust handling of expired/invalid tokens
- **Accessibility:** Needs more ARIA labels and keyboard navigation
- **Testing:** More unit and integration tests for UI flows

---

## 5. Debugging & Testing Tips
- Use the debug logs in GmailConnectModal and OAuthCallbackPage
- Always validate OAuth state to prevent CSRF
- Test in incognito and with localStorage/sessionStorage fallbacks
- See `FRONTEND_OAUTH_CHECKLIST.md` for manual and security test cases 