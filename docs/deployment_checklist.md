# Deployment Checklist

Follow this checklist to redeploy TidyMail from scratch or on a new environment.

---

## 1. Required Accounts & Credentials
- Google Cloud project (Gmail API, Pub/Sub enabled)
- Clerk.dev account (for authentication)
- MongoDB URI (local or Atlas)
- Gemini API key (or OpenAI key if swapping)

---

## 2. Environment Variables (.env)
Create a `.env` file in the backend root with:

```
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/gmail/oauth/callback
GOOGLE_PROJECT_ID=your_google_project_id

# Clerk
CLERK_FRONTEND_API=your_clerk_frontend_api
CLERK_SECRET_KEY=your_clerk_secret_key
FRONTEND_URL=http://localhost:3000

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=email_categorizer
MONGODB_OAUTH_COLLECTION_NAME=oauth

# AI
GEMINI_API_KEY=your_gemini_api_key
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent

# Session
SESSION_SECRET_KEY=your_session_secret_key
```

---

## 3. Build Tools & Dependencies
- **Python 3.12+**
- **Node.js** (for frontend)
- **Rust** (for pydantic-core):
  - `winget install Rustlang.Rustup`
- **Microsoft C++ Build Tools** (for Windows):
  - Download from https://visualstudio.microsoft.com/visual-cpp-build-tools/
  - Select "Desktop development with C++", Windows 10/11 SDK, MSVC v143, CMake tools

---

## 4. ngrok Setup (for Webhook Testing)
- Download from https://ngrok.com/download
- Run: `ngrok http 8000`
- Update Google Pub/Sub push endpoint to use your ngrok URL

---

## 5. Clerk.dev Integration
- Set up Clerk application and get API keys
- User JWTs are sent as `Authorization: Bearer <token>` to backend
- User metadata (MongoDB):
  - `clerk_user_id`, `email`, `is_gmail_connected`, `gmail_email`, `gmail_connected_at`
- Backend uses Clerk JWT to identify and authorize users

---

## 6. MongoDB
- Set up a database and update `MONGODB_URI` in `.env`
- Collections: `users`, `emails`, `oauth`

---

## 7. Google Cloud Setup
- Enable Gmail API and Pub/Sub
- Create OAuth 2.0 credentials (Web application)
- Add redirect URI
- Set up Pub/Sub topic and push subscription (see `gmail_setup.md`)
- Create and configure service account for Pub/Sub

---

## 8. Running Locally
```bash
# Backend
python -m venv venv_py312
.\venv_py312\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm start
```

---

## 9. Deployment (Cloud)
- Set all environment variables in your deployment platform (Render, Heroku, Vercel, etc.)
- Use HTTPS for all OAuth and webhook endpoints
- Update Pub/Sub push endpoint to your deployed backend

---

## 10. Troubleshooting
- If pydantic-core fails to build: check Python, Rust, and C++ build tools
- If OAuth fails: check redirect URIs, client secrets, and consent screen
- If webhooks fail: check ngrok/endpoint, Pub/Sub permissions, and logs 