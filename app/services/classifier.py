import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def classify_email(subject: str, body: str, return_prompt_and_model: bool = False):
    """
    Classify an email into predefined categories using Gemini Pro API.
    If return_prompt_and_model is True, also return the prompt and model used.
    """
    # Get API key from environment variables
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        if return_prompt_and_model:
            return ("Error: GEMINI_API_KEY not found in environment variables", None, None)
        return "Error: GEMINI_API_KEY not found in environment variables"

    # API endpoint
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    model = "gemini-2.0-flash"
    # Prepare the prompt
    prompt = f"""You are an email classifier. Your task is to carefully analyze the email content and categorize it into exactly one of these categories:\n\n- Internship\n- Job Offer\n- Funding\n- Product Review\n- Newsletter\n- Event Invitation\n- Meeting Request\n- Research Article Request\n- Spam / Promotion\n- General Inquiry\n- Security Alert (for account security notifications, login alerts, password changes, etc.)\n\nImportant Instructions:\n1. Read the ENTIRE email body thoroughly - do not rely solely on the subject line\n2. Subjects can be misleading - always verify the actual content in the body\n3. Look for key details in the body that indicate the true purpose of the email\n4. Consider the context and tone of the entire message\n5. If the email could fit multiple categories, choose the most specific one\n6. Pay special attention to security-related emails (login alerts, password changes, etc.)\n7. Return ONLY the category name, nothing else\n\nEmail Subject:\n{subject}\n\nEmail Body:\n{body}\n\nCategory:"""

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        if 'candidates' in result and len(result['candidates']) > 0:
            category = result['candidates'][0]['content']['parts'][0]['text'].strip()
            if return_prompt_and_model:
                return (category, prompt, model)
            return category
        else:
            if return_prompt_and_model:
                return ("Error: Unexpected API response format", prompt, model)
            return "Error: Unexpected API response format"
    except requests.exceptions.RequestException as e:
        if return_prompt_and_model:
            return (f"Error: API request failed - {str(e)}", prompt, model)
        return f"Error: API request failed - {str(e)}"
    except (KeyError, IndexError) as e:
        if return_prompt_and_model:
            return (f"Error: Failed to parse API response - {str(e)}", prompt, model)
        return f"Error: Failed to parse API response - {str(e)}"
    except Exception as e:
        if return_prompt_and_model:
            return (f"Error: An unexpected error occurred - {str(e)}", prompt, model)
        return f"Error: An unexpected error occurred - {str(e)}"