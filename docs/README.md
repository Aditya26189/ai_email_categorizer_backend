# TidyMail: AI-Powered Email Management

TidyMail is an AI-powered email management tool that connects with Gmail, categorizes incoming emails, summarizes them using AI, and stores results in MongoDB. It features a modern React + Tailwind frontend, a FastAPI backend, secure Gmail OAuth integration, real-time Pub/Sub webhook notifications, and AI summarization/classification.

## Core Goals
- Help users quickly triage and understand their inbox
- Provide smart, AI-generated summaries and categories for each email
- Make it easy to extend, redeploy, or continue development in the future

## Who is this for?
- Anyone overwhelmed by email volume
- Developers looking to build on a modern, full-stack AI email platform
- Teams needing a customizable, private AI email assistant

## Tech Stack
- **Frontend:** React, Tailwind CSS
- **Backend:** FastAPI (Python 3.12+)
- **Database:** MongoDB
- **Authentication:** Clerk.dev (JWTs)
- **AI:** Gemini API (Google), easily swappable for OpenAI
- **Gmail Integration:** OAuth 2.0, Google Pub/Sub, Webhooks

## Setup Instructions

### 1. Prerequisites
- Python 3.12+
- Node.js (for frontend)
- MongoDB (local or Atlas)
- Google Cloud project with Gmail API & Pub/Sub enabled
- Clerk.dev account
- Gemini API key (or OpenAI key if swapping)

### 2. Environment Variables
Create a `.env` file in the backend root:

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

### 3. Gmail API Setup
- Create a Google Cloud project
- Enable Gmail API
- Create OAuth 2.0 credentials (Web application)
- Add your backend's redirect URI
- Set up Pub/Sub topic for Gmail events (see `gmail_setup.md`)

### 4. Clerk Setup
- Create a Clerk application
- Configure authentication and webhooks

### 5. Install Dependencies
```bash
# Backend
python -m venv venv_py312
.\venv_py312\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 6. Running Locally
```bash
# Backend
uvicorn app.main:app --reload

# Frontend
cd frontend
npm start
```

### 7. Webhook Testing (ngrok)
- Download ngrok from https://ngrok.com/download
- Run: `ngrok http 8000`
- Update your Google Pub/Sub push endpoint to use the ngrok URL

## Deployment Tips
- Use Render, Heroku, or Vercel for backend/frontend
- Set all environment variables in your deployment platform
- Use HTTPS for all OAuth and webhook endpoints
- For webhooks, update Pub/Sub to point to your deployed backend

## Known Limitations
- Gmail restricted scopes may require Google verification for production
- AI summarization depends on Gemini API limits and reliability
- No calendar/reminder integration yet
- Some UI features may be incomplete (see `frontend_notes.md`)

## Future Plans
- Add reminders and follow-up suggestions
- Calendar sync and smart scheduling
- More robust error handling and retry logic
- Enhanced analytics and user settings

For full architecture, API, and deployment details, see the rest of the docs folder. 