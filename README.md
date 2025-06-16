# AI Email Categorizer API

A FastAPI-based service that categorizes emails using AI.

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
MONGODB_COLLECTION_NAME=

```

Note: All these variables are required. The application will not start without them.

## Running the Application

Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
ai_email_categorizer/
├── app/
│   ├── core/           # Core functionality
│   │   ├── config.py   # Configuration
│   │   ├── logger.py   # Logging setup
│   │   ├── middleware.py # Middleware configuration
│   │   └── dependencies.py # API dependencies
│   ├── models/         # Data models
│   ├── routers/        # API routes
│   ├── services/       # Business logic
│   └── utils/          # Utility functions
├── tests/              # Test files
├── .env               # Environment variables
├── requirements.txt   # Dependencies
└── README.md         # This file
```

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