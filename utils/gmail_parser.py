import base64
import quopri
import html
import re
from bs4 import BeautifulSoup

def decode_email_body(data: str) -> str:
    """
    Decodes a Gmail API base64url encoded string into readable text.
    Handles both base64 and quoted-printable encoding.
    """
    if not data:
        return ""
    try:
        # Try base64 decoding first
        decoded_bytes = base64.urlsafe_b64decode(data + '=' * (4 - len(data) % 4))
        decoded_text = decoded_bytes.decode("utf-8", errors="replace")
        
        # Check if the result looks like quoted-printable and decode if needed
        if "=3D" in decoded_text or "=\r\n" in decoded_text:
            decoded_text = quopri.decodestring(decoded_text).decode("utf-8", errors="replace")
            
        return decoded_text
    except Exception as e:
        return f"[Decoding Error] {e}"

def extract_email_body(payload: dict) -> str:
    """
    Extracts the email body (preferably HTML, fallback to plain text) from Gmail message payload.
    Handles nested multipart messages properly.
    """
    def find_parts(parts):
        html_content = None
        plain_content = None
        
        for part in parts:
            mime_type = part.get("mimeType", "")
            body_data = part.get("body", {}).get("data", "")
            decoded = decode_email_body(body_data)

            if mime_type == "text/html":
                html_content = clean_html(decoded)
            elif mime_type == "text/plain":
                plain_content = clean_plain_text(decoded)
            elif mime_type.startswith("multipart"):
                # Recurse into sub-parts
                sub_parts = part.get("parts", [])
                sub_result = find_parts(sub_parts)
                if sub_result:
                    return sub_result
        
        # Return HTML if available, otherwise plain text
        return html_content if html_content else plain_content

    if "parts" in payload:
        result = find_parts(payload["parts"])
        if result:
            return result
    else:
        # No parts — check if full body is in payload
        body_data = payload.get("body", {}).get("data", "")
        return decode_email_body(body_data)
    
    return "[No content found]"

def clean_plain_text(text: str) -> str:
    """
    Clean plain text content by removing encoding artifacts and normalizing whitespace.
    """
    if not text:
        return ""
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Fix common encoding artifacts (e.g., â€™ becomes apostrophe)
    text = text.encode('latin1', errors='ignore').decode('utf-8', errors='ignore')
    
    # Remove zero-width spaces and other invisible characters
    text = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\u202a-\u202e]', '', text)
    
    # Remove non-breaking spaces and replace with regular spaces
    text = text.replace('\u00A0', ' ')
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text.strip()

def clean_html(html_content: str) -> str:
    """
    Clean HTML content using BeautifulSoup and handle encoding artifacts.
    """
    if not html_content:
        return ""
    
    try:
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'meta', 'link']):
            element.decompose()
        
        # Get text content
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean the extracted text
        text = clean_plain_text(text)
        
        # Remove multiple spaces and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
        
    except Exception as e:
        return f"[HTML parse error] {e}" 