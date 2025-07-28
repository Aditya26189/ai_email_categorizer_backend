import os
import time
import requests
from dotenv import load_dotenv
from app.core.api_logging import email_logger

# Load environment variables from .env file
load_dotenv()

def classify_email(subject: str, body: str) -> str:
    """
    Classify an email into predefined categories using Gemini Pro API.
    
    Args:
        subject (str): The email subject
        body (str): The email body
        
    Returns:
        str: The classified category or error message
    """
    start_time = time.time()
    
    # Get API key from environment variables
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return "Error: GEMINI_API_KEY not found in environment variables"

    # API endpoint
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    # Prepare the prompt
    prompt = f"""You are an email classifier. Your task is to carefully analyze the email content and categorize it into exactly one of these categories:

- Internship
- Job Offer
- Funding
- Product Review
- Newsletter
- Event Invitation
- Meeting Request
- Research Article Request
- Spam / Promotion
- General Inquiry
- Security Alert (for account security notifications, login alerts, password changes, etc.)

Important Instructions:
1. Read the ENTIRE email body thoroughly - do not rely solely on the subject line
2. Subjects can be misleading - always verify the actual content in the body
3. Look for key details in the body that indicate the true purpose of the email
4. Consider the context and tone of the entire message
5. If the email could fit multiple categories, choose the most specific one
6. Pay special attention to security-related emails (login alerts, password changes, etc.)
7. Return ONLY the category name, nothing else

Email Subject:
{subject}

Email Body:
{body}

Category:"""

    # Prepare the request payload
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    # Set up headers with API key
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    try:
        # Make the API request
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the response
        result = response.json()
        
        # Extract the category from the response
        if 'candidates' in result and len(result['candidates']) > 0:
            category = result['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # Log the classification
            processing_time_ms = int((time.time() - start_time) * 1000)
            email_logger.log_email_classification(
                email_subject=subject,
                email_body=body,
                predicted_category=category,
                model_used="gemini-2.0-flash",
                processing_time_ms=processing_time_ms
            )
            
            return category
        else:
            return "Error: Unexpected API response format"
            
    except requests.exceptions.RequestException as e:
        return f"Error: API request failed - {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Error: Failed to parse API response - {str(e)}"
    except Exception as e:
        return f"Error: An unexpected error occurred - {str(e)}"