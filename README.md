# AI Email Categorizer

## Project Structure
```
app/
├── core/
│   ├── __init__.py
│   ├── config.py          # Application configuration
│   ├── dependencies.py    # API dependencies
│   ├── logger.py          # Logging configuration
│   ├── middleware.py      # Custom middleware
│   └── oauth.py           # OAuth configuration
├── models/
│   ├── __init__.py
│   └── schema.py          # SQLAlchemy models
├── routers/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py     # Authentication routes
│   │   ├── services.py   # Auth business logic
│   │   └── validators.py # Request/response models
│   ├── email_routes.py   # Email-related endpoints
│   ├── classify_routes.py # Classification endpoints
│   └── health_routes.py  # Health check endpoints
├── services/
│   ├── __init__.py
│   ├── classifier.py     # Email classification logic
│   ├── gmail_client.py   # Gmail API integration
│   └── storage.py        # Data storage operations
├── utils/
│   ├── __init__.py
│   ├── gmail_parser.py   # Gmail message parsing utilities
│   └── llm_utils.py      # LLM integration utilities
└── main.py              # FastAPI application entry point
```

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
SECRET_KEY=your_secret_key
MONGODB_URI=your_mongodb_uri
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation
Once the application is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Features

- Email categorization using AI
- RESTful API endpoints
- API key authentication
- Logging and monitoring
- Modular architecture
- MongoDB cloud storage

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

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:

Required Variables:
```env

# Gmail Configuration
GMAIL_CREDENTIALS_FILE=
GMAIL_TOKEN_FILE=

# Gemini AI Configuration
GEMINI_API_KEY=
GEMINI_API_URL=

# MongoDB Configuration
MONGODB_URI=
MONGODB_DB_NAME=
MONGODB_EMAIL_COLLECTION_NAME=
MONGODB_USERS_COLLECTION_NAME

```

Note: All these variables are required. The application will not start without them.

## Running the Application

Start the server:
```bash
uvicorn app.main:app --reload
```
to test the user updating the info 
choco install ngrok

The API will be available at `http://localhost:8000`

## Development

### Running Tests
```bash
pytest
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

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 