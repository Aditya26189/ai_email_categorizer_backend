import json
from datetime import datetime
import os
from typing import List, Dict, Optional

STORAGE_FILE = 'classified_emails.json'

def load_emails() -> List[Dict]:
    """
    Load all classified emails from the JSON storage file.
    
    Returns:
        List[Dict]: List of email dictionaries, or empty list if file doesn't exist
    """
    if not os.path.exists(STORAGE_FILE):
        return []
    
    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If file is corrupted, return empty list
        return []
    except Exception as e:
        print(f"Error loading emails: {str(e)}")
        return []

def save_email(email_dict: Dict) -> bool:
    """
    Save a classified email to the JSON storage file.
    Only saves if the email subject is not already present.
    
    Args:
        email_dict (Dict): Dictionary containing email data with at least 'subject' key
        
    Returns:
        bool: True if email was saved, False if it was a duplicate or error occurred
    """
    try:
        # Load existing emails
        emails = load_emails()
        
        # Check for duplicate subject
        if any(email.get('subject') == email_dict.get('subject') for email in emails):
            return False
        
        # Add timestamp
        email_dict['timestamp'] = datetime.utcnow().isoformat()
        
        # Append new email
        emails.append(email_dict)
        
        # Save back to file
        with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(emails, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        print(f"Error saving email: {str(e)}")
        return False

def get_email_by_subject(subject: str) -> Optional[Dict]:
    """
    Retrieve a specific email by its subject.
    
    Args:
        subject (str): The email subject to search for
        
    Returns:
        Optional[Dict]: The email dictionary if found, None otherwise
    """
    emails = load_emails()
    for email in emails:
        if email.get('subject') == subject:
            return email
    return None

if __name__ == '__main__':
    # Test the storage functionality
    test_email = {
        'subject': 'Test Email',
        'body': 'This is a test email body',
        'category': 'General Inquiry'
    }
    
    # Save test email
    if save_email(test_email):
        print("Test email saved successfully")
    else:
        print("Failed to save test email or it was a duplicate")
    
    # Load and print all emails
    all_emails = load_emails()
    print(f"\nTotal emails in storage: {len(all_emails)}")
    for email in all_emails:
        print(f"\nSubject: {email.get('subject')}")
        print(f"Category: {email.get('category')}")
        print(f"Timestamp: {email.get('timestamp')}") 