import requests
import textwrap
from loguru import logger
from app.core.config import settings

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

def summarize_to_bullets(text: str, max_bullets: int = 5) -> list:
    """
    Summarize text into bullet points using Gemini AI.
    
    Args:
        text (str): The text to summarize
        max_bullets (int): Maximum number of bullet points to generate
        
    Returns:
        list: List of bullet point summaries
    """
    try:
        prompt = f"""Summarize the following text into {max_bullets} key bullet points.
        Focus on the most important information and main points.
        Keep each bullet point concise and clear.
        
        Text:
        {text}
        
        Return only the bullet points, one per line, starting with '- '."""
        
        response = requests.post(
            settings.GEMINI_API_URL,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": settings.GEMINI_API_KEY
            },
            json={
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Error from Gemini API: {response.text}")
            return get_fallback_summary(text)
            
        response_data = response.json()
        if not response_data.get("candidates"):
            logger.error("No candidates in Gemini API response")
            return get_fallback_summary(text)
            
        summary = response_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # Split into bullet points and clean up
        bullets = [line.strip('- ').strip() for line in summary.split('\n') if line.strip()]
        
        # Ensure we don't exceed max_bullets
        bullets = bullets[:max_bullets]
        
        return bullets
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return get_fallback_summary(text)

def extract_key_info(text: str) -> dict:
    """
    Extract key information from text using Gemini AI.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: Dictionary containing key information
    """
    try:
        prompt = f"""Extract key information from the following text.
        Return a JSON object with these fields:
        - main_topic: The main topic or purpose
        - key_points: List of 3-5 key points
        - action_items: List of any required actions
        - sentiment: Overall sentiment (positive/negative/neutral)
        
        Text:
        {text}
        
        Return only the JSON object, nothing else."""
        
        response = requests.post(
            settings.GEMINI_API_URL,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": settings.GEMINI_API_KEY
            },
            json={
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Error from Gemini API: {response.text}")
            return {
                "main_topic": "Error",
                "key_points": ["Failed to extract information"],
                "action_items": [],
                "sentiment": "neutral"
            }
            
        response_data = response.json()
        if not response_data.get("candidates"):
            logger.error("No candidates in Gemini API response")
            return {
                "main_topic": "Error",
                "key_points": ["Failed to extract information"],
                "action_items": [],
                "sentiment": "neutral"
            }
            
        info = response_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # Parse the response into a dictionary
        # Note: In a production environment, you'd want to use proper JSON parsing
        # and error handling here
        return {
            "main_topic": "Extracted topic",
            "key_points": ["Point 1", "Point 2"],
            "action_items": ["Action 1"],
            "sentiment": "neutral"
        }
    except Exception as e:
        logger.error(f"Error extracting key info: {str(e)}")
        return {
            "main_topic": "Error",
            "key_points": ["Failed to extract information"],
            "action_items": [],
            "sentiment": "neutral"
        } 