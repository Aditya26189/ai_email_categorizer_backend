# AI Email Categorizer

A FastAPI-based application that uses AI to automatically categorize and summarize emails from Gmail with secure OAuth integration.

## Features

- 🔐 **Clerk Authentication**: Secure user authentication and management
- 📧 **Gmail OAuth Integration**: Full Gmail client capabilities with OAuth 2.0
- 🤖 **AI Classification**: Automatic email categorization using Gemini AI
- 📝 **Smart Summarization**: AI-powered email summarization
- 🔄 **Real-time Processing**: Push notifications for new emails
- 💾 **MongoDB Storage**: Scalable email and user data storage
- 🚀 **FastAPI Backend**: High-performance REST API

## Gmail OAuth Integration

This application implements a complete Gmail OAuth flow with the following capabilities:

### 🔧 OAuth Configuration

The OAuth integration supports all Gmail client capabilities with these scopes:

```python
GMAIL_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.settings.basic"
]
```

# use python 3.12
# download ngrok for local testing webhook from clerk and gmail -> 
- choco install ngrok
- ngrok config add-authtoken 2yjRMK9Yf7Af52zUtx92W6UBYNT_5944VTZw8d1uMEfuBSCT
- ngrok http http://localhost:8080
if not given permission use this command
```md
Set-ExecutionPolicy Bypass -Scope Process -Force; `
>> [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; `
>> iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

### 🔄 Complete OAuth Workflow

#### 1. User Authentication
- User signs into your app (via Clerk or other auth)
- You already have the user_id (e.g. user_2xYk...) from Clerk
- This user ID is stored in your database

#### 2. Check Gmail Connection Status
- Store `is_gmail_connected: true/false` flag for each user in MongoDB
- When `is_gmail_connected == false`, user has not granted Gmail access yet

#### 3. Frontend: Show Gmail Connect Popup
When you detect `is_gmail_connected === false`:

```typescript
if (!user.is_gmail_connected) {
  // Show UI modal or button:
  // "Connect your Gmail account to enable smart email summaries"
}
```

The Connect Gmail button triggers a call to your backend:
```http
GET /gmail/oauth/start?user_id=<clerk_user_id>
```

#### 4. Backend: Redirect to Google OAuth
This endpoint (`/gmail/oauth/start`) builds a Gmail OAuth URL and redirects the user.

#### 5. User Grants Access → Redirects to /gmail/oauth/callback
Google sends back a code and state to your `/gmail/oauth/callback` route.

Your backend uses this code to:
- Exchange it for access_token, refresh_token
- Save these tokens in MongoDB tied to user_id
- Set `is_gmail_connected = true`

#### 6. Done ✅
Now you can:
- Start the Gmail Watch API (`/gmail/watch/setup`)
- Ingest and summarize emails
- Use the refresh token for long-term access

#### 🔁 Future Logins
When the user logs into your app again:
- You check `is_gmail_connected` again
- If true, no need to show popup
- If false, show the popup again

### 🗄️ Data Storage Structure

#### Users Collection
```json
{
  "clerk_user_id": "user_2xYk...",
  "email": "someone@gmail.com",
  "is_gmail_connected": true,
  "gmail_email": "user@gmail.com",
  "gmail_connected_at": "2025-06-21T10:00:00Z",
  "updated_at": "2025-06-21T10:00:00Z"
}
```

#### OAuth Collection
```json
{
  "user_id": "user_2xYk...",
  "google_user_id": "google_user_456", 
  "email": "user@example.com",
  "name": "User Name",
  "access_token": "ya29.a0...",
  "refresh_token": "1//04...",
  "expires_at": "2025-06-21T12:00:00Z",
  "scopes": ["openid", "email", "profile", ...],
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "created_at": "2025-06-21T10:00:00Z",
  "updated_at": "2025-06-21T10:00:00Z"
}
```

### 📡 Gmail Push Notifications

- **Watch Setup**: `/gmail/watch/setup`
  - Configures Gmail push notifications for INBOX
  - Uses Google Cloud Pub/Sub for real-time email events
  - Automatically triggered after OAuth completion

- **Webhook Receiver**: `/webhook/gmail`
  - Receives push notifications when new emails arrive
  - Triggers email processing pipeline
  - Processes and categorizes new emails automatically

### ✅ Summary: What Triggers the Gmail Popup?

| Condition | Action |
|-----------|--------|
| `user.is_gmail_connected == false` | Show Gmail Connect modal on frontend |
| Click "Connect" | Redirect to Google OAuth flow |
| User grants access | Backend receives token, updates DB |
| `is_gmail_connected == true` | App fetches emails and starts Watch |

## Project Structure
```
app/
├── core/
│   ├── __init__.py
│   ├── config.py          # Application configuration
│   ├── dependencies.py    # API dependencies
│   ├── logger.py          # Logging configuration
│   ├── middleware.py      # Custom middleware
│   └── clerk.py           # Clerk authentication
├── models/
│   ├── __init__.py
│   ├── email.py           # Email models
│   └── user.py            # User models
├── routers/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── auth_routes.py # Authentication routes
│   │   ├── clerk_webhook.py # Clerk webhook handling
│   │   └── gmail_auth.py  # Gmail auth routes
│   ├── email_routes.py    # Email-related endpoints
│   ├── classify_routes.py # Classification endpoints
│   ├── gmail.py           # Gmail OAuth routes
│   ├── health_routes.py   # Health check endpoints
│   └── webhook.py         # Gmail webhook receiver
├── services/
│   ├── __init__.py
│   ├── classifier.py      # Email classification logic
│   ├── gmail_client.py    # Gmail API integration
│   ├── google_oauth.py    # Google OAuth service
│   ├── token_refresh.py   # Token refresh logic
│   ├── email_ingestion.py # Email processing pipeline
│   └── user_sync.py       # User synchronization
├── utils/
│   ├── __init__.py
│   ├── gmail_parser.py    # Gmail message parsing utilities
│   └── llm_utils.py       # LLM integration utilities
└── main.py               # FastAPI application entry point
```

## Environment Variables

Add these to your `.env` file:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/gmail/oauth/callback
GOOGLE_PROJECT_ID=your_google_project_id

# Clerk Authentication
CLERK_FRONTEND_API=your_clerk_frontend_api
CLERK_SECRET_KEY=your_clerk_secret_key
FRONTEND_URL=http://localhost:3000

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=email_categorizer
MONGODB_OAUTH_COLLECTION_NAME=oauth

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key

# Session Configuration
SESSION_SECRET_KEY=your_session_secret_key
```

## API Endpoints

### OAuth Endpoints

- `GET /gmail/oauth/url` - Generate OAuth authorization URL
- `GET /gmail/oauth/callback` - Handle OAuth callback
- `GET /gmail/oauth/status` - Check OAuth connection status
- `DELETE /gmail/oauth/revoke` - Revoke OAuth access
- `POST /gmail/watch/setup` - Set up Gmail push notifications

### Email Endpoints

- `GET /routers/v1/emails/emails` - Get user's emails with filtering
- `GET /routers/v1/emails/by-categories` - Get emails grouped by category
- `POST /routers/v1/classify/` - Classify and store a single email
- `GET /routers/v1/classify/emails` - Fetch and process latest emails

### Webhook Endpoints

- `POST /webhook/gmail` - Receive Gmail push notifications

## Setup Instructions

### 1. Google Cloud Console Setup

1. Create a new project in Google Cloud Console
2. Enable Gmail API
3. Create OAuth 2.0 credentials (Web application)
4. Add authorized redirect URIs
5. Set up Pub/Sub topic for Gmail events

### 2. Clerk Setup

1. Create a Clerk application
2. Configure authentication settings
3. Set up webhook endpoints if needed

### 3. Application Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables
3. Start the application: `python -m app.main`

## Usage Flow

1. **User Authentication**: User signs in via Clerk
2. **Gmail Connection**: User initiates Gmail OAuth flow
3. **Authorization**: User grants Gmail permissions
4. **Setup Complete**: OAuth credentials stored, push notifications configured
5. **Real-time Processing**: New emails automatically processed and categorized

## Security Features

- **Secure Token Storage**: OAuth tokens encrypted in MongoDB
- **Automatic Token Refresh**: Handles token expiration seamlessly
- **User Isolation**: Each user's emails and credentials isolated
- **Clerk Integration**: Enterprise-grade authentication
- **HTTPS Required**: All OAuth flows require HTTPS in production

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai_email_categorizer.git
cd ai_email_categorizer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env` file

## Running the Application

Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## Development

### Running Tests
```bash
pytest tests/test_google_oauth.py -v
```

### Code Formatting
```bash
black .
isort .
```

### Linting
```bash
flake8
```

## Logging

Logs are stored in the `logs` directory:
- Console output for development
- `logs/app.log` for persistent logging
- Automatic log rotation (500MB)
- 1-week retention period


## how to set up commands for dependencies downloads ( also change python interpreter to the venv_312 by ctrl+sft+p after creating the venv_py312 folder )

```powershell
 py -3.12 -m venv venv_py312   
 Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\venv_py312\Scripts\activate
  pip install -r requirements.txt
  uvicorn app.main:app --reload
```





## what things to download before running, as would cause pydantic error with the latest version

<aside>
💡

have the python 3.12 version

</aside>

```powershell
 winget install Rustlang.Rustup
```

> go to [Microsoft C++ Build Tools - Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/) and download the build tools
> 

> run the installer and select the
> 
> 
> For building Python packages on Windows, you need to select these components in the Visual Studio Build Tools installer:
> 
> 1. "Desktop development with C++" workload
> - This is the main component you need
> 1. Under Individual Components tab, make sure to select:
> - Windows 10/11 SDK
> - MSVC v143 - VS 2022 C++ x64/x86 build tools
> - C++ CMake tools for Windows
> 
> The minimum selection should be:
> 
> - ✓ Desktop development with C++
> - ✓ Windows 10/11 SDK
> - ✓ MSVC v143 - VS 2022 C++ x64/x86 build tools
> 
> This will give you the necessary C++ compiler and build tools needed for installing Python packages that require compilation, like pydantic-core and other packages with Rust components.
> 
> After installing these, you'll need to restart your terminal/command prompt for the changes to take effect.
>



## Links for the google setup

[gmail-events – Pub/Sub – Email AI Auth – Google Cloud console](https://console.cloud.google.com/cloudpubsub/subscription/detail/gmail-events?authuser=1&inv=1&invt=Ab0o6A&project=second-sandbox-463119-k3&tab=overview&pageState=(%22duration%22:(%22groupValue%22:%22PT1H%22,%22customValue%22:null)))

[Google Cloud console](https://console.cloud.google.com/apis/credentials?authuser=1&inv=1&invt=Ab0cmQ&project=second-sandbox-463119-k3)  → api and services

[Service accounts – IAM & Admin – Email AI Auth – Google Cloud console](https://console.cloud.google.com/iam-admin/serviceaccounts?authuser=1&inv=1&invt=Ab0sLg&project=second-sandbox-463119-k3&supportedpurview=project)
