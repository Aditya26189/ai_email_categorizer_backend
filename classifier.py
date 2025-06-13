import os
import requests
from dotenv import load_dotenv

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
    # Get API key from environment variables
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return "Error: GEMINI_API_KEY not found in environment variables"

    # API endpoint (updated for Gemini 2.0 Flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    # Prepare the prompt
    prompt = f"""Please classify the following email into exactly one of these categories:
    - Internship Application
    - Job Offer
    - Funding Request
    - Product Review Request
    - Article Submission
    - Partnership Inquiry
    - Meeting Request
    - Legal/Compliance
    - Order Notification
    - Customer Feedback

    Email Subject: {subject}
    Email Body: {body}

    Return ONLY the category name, nothing else."""

    # Prepare the request payload
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    # Set up headers (no API key needed in header for this endpoint)
    headers = {
        "Content-Type": "application/json"
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
            return category
        else:
            return "Error: Unexpected API response format"
            
    except requests.exceptions.RequestException as e:
        return f"Error: API request failed - {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Error: Failed to parse API response - {str(e)}"
    except Exception as e:
        return f"Error: An unexpected error occurred - {str(e)}"