import os
import requests
from dotenv import load_dotenv
import textwrap

# Load environment variables
load_dotenv()

# Get API key from environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def get_fallback_summary(text: str, max_length: int = 200) -> list[str]:
    """
    Generate a fallback summary when AI summarization fails.
    Returns first few sentences or a truncated version of the text.
    """
    # Split into sentences (rough approximation)
    sentences = text.split('.')
    summary = []
    
    # Add first two meaningful sentences
    for sentence in sentences:
        if len(sentence.strip()) > 20:  # Only meaningful sentences
            summary.append(sentence.strip() + '.')
            if len(summary) >= 2:
                break
    
    # If no good sentences found, return truncated text
    if not summary:
        truncated = textwrap.shorten(text, width=max_length, placeholder='...')
        summary = [truncated]
    
    return summary

def summarize_to_bullets(email_text: str, force_regenerate: bool = False) -> list[str]:
    """
    Summarize email content into concise bullet points using Gemini AI.
    Falls back to basic text extraction if AI fails.
    
    Args:
        email_text (str): The email content to summarize
        force_regenerate (bool): If True, forces regeneration even if cached
        
    Returns:
        list[str]: List of bullet points summarizing the email
    """
    if not email_text:
        return ["[No content to summarize]"]
        
    try:
        # Create the prompt
        prompt = f"""You are a helpful assistant that summarizes emails.

Summarize the following email into 3-5 clear and concise bullet points so the user can quickly understand the content.
Focus on the most important information, key actions required, and main points.

EMAIL:
\"\"\"
{email_text}
\"\"\"

Return only the bullet points, one per line, starting with a bullet point character (- or •).
Keep each point brief but informative.
"""

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
            "x-goog-api-key": GEMINI_API_KEY
        }

        # Make the API request
        response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the response
        result = response.json()
        
        # Extract the text from the response
        if 'candidates' in result and len(result['candidates']) > 0:
            text = result['candidates'][0]['content']['parts'][0]['text']
            # Process the response into bullet points
            bullets = [line.strip("-• ").strip() for line in text.splitlines() if line.strip()]
            
            # Ensure we have at least one bullet point
            if bullets:
                return bullets
        
        # If we get here, something went wrong with the response
        return get_fallback_summary(email_text)
            
    except Exception as e:
        print(f"Error generating AI summary: {str(e)}")
        return get_fallback_summary(email_text) 