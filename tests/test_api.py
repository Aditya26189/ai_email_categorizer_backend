import requests
import json
from datetime import datetime

def test_classify_endpoint():
    # API endpoint URL
    url = "http://localhost:8000/classify"
    
    # Sample email data (updated for new Email schema)
    data = {
        "gmail_id": "1853d239248aee99",
        "thread_id": "1853d239248aee22",
        "history_id": "7892310",
        "label_ids": ["INBOX", "IMPORTANT"],
        "subject": "Meeting Request: Project Kickoff",
        "body": """
        Hi Team,
        
        I hope this email finds you well. I'd like to schedule a meeting to discuss the kickoff of our new project.
        Please let me know your availability for next week.
        
        Best regards,
        John
        """,
        "category": "Meeting Request",
        "summary": ["Request to schedule a project kickoff meeting", "Asking for team availability"],
        "sender": "john.doe@example.com",
        "timestamp": "2024-02-20T12:00:00Z",
        "internal_date": "1700000000000",
        "is_read": False,
        "is_processed": True,
        "is_sensitive": False,
        "status": "new",
        "fetched_at": "2024-02-20T14:00:00Z",
        "user_id": "user_abc123"
    }
    
    try:
        # Send POST request
        response = requests.post(url, json=data)
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse and print the response
        result = response.json()
        print("\nClassification Result:")
        print(json.dumps(result, indent=2))
        # Assert new fields in response
        for field in [
            "gmail_id", "thread_id", "history_id", "label_ids", "category", "summary", "sender", "timestamp", "internal_date", "is_read", "is_processed", "is_sensitive", "status", "fetched_at", "user_id"
        ]:
            assert field in result, f"Response should include {field}"
    
    except requests.exceptions.RequestException as e:
        print(f"\nError occurred: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response details: {e.response.text}")

def test_categories_endpoint():
    """Test the email categories endpoint."""
    base_url = "http://localhost:8000/emails/categories"
    
    try:
        # Test with default limit (5)
        response = requests.get(base_url)
        response.raise_for_status()
        result = response.json()
        print("\nCategories Result (default limit):")
        print(json.dumps(result, indent=2))
        
        # Verify the response structure and default limit
        assert isinstance(result, dict), "Response should be a dictionary"
        for category, emails in result.items():
            assert isinstance(emails, list), f"Emails for category {category} should be a list"
            assert len(emails) <= 5, f"Category {category} should have at most 5 emails"
            for email in emails:
                # Assert new fields in each email
                for field in [
                    "gmail_id", "thread_id", "history_id", "label_ids", "category", "summary", "sender", "timestamp", "internal_date", "is_read", "is_processed", "is_sensitive", "status", "fetched_at", "user_id"
                ]:
                    assert field in email, f"Each email should have {field}"
        
        # Test with custom limit (3)
        response = requests.get(f"{base_url}?limit=3")
        response.raise_for_status()
        result = response.json()
        print("\nCategories Result (limit=3):")
        print(json.dumps(result, indent=2))
        
        # Verify the custom limit
        for category, emails in result.items():
            assert len(emails) <= 3, f"Category {category} should have at most 3 emails"
        
        # Test with invalid limit (should use default)
        response = requests.get(f"{base_url}?limit=0")
        response.raise_for_status()
        result = response.json()
        for category, emails in result.items():
            assert len(emails) <= 5, f"Category {category} should have at most 5 emails with invalid limit"
        
    except requests.exceptions.RequestException as e:
        print(f"\nError occurred: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response details: {e.response.text}")

def test_register_user():
    url = "http://localhost:8000/routers/v1/auth/register"
    user_data = {
        "clerk_id": "user_abc123",
        "email": "user@example.com",
        "name": "John Doe",
        "picture": "https://example.com/avatar.jpg",
        "gmail_connected": True,
        "gmail_email": "john@gmail.com",
        "gmail_tokens": {
            "access_token": "ya29.a0AfH6S...",
            "refresh_token": "1//0gL4...",
            "expires_at": 1720000000
        },
        "created_at": datetime.utcnow().isoformat()
    }
    response = requests.post(url, json=user_data)
    assert response.status_code == 200, f"Register failed: {response.text}"
    result = response.json()
    print("\nRegister User Result:")
    print(json.dumps(result, indent=2))
    for field in ["clerk_id", "email", "name", "picture", "gmail_connected", "gmail_email", "gmail_tokens", "created_at"]:
        assert field in result, f"User response missing {field}"

def test_get_me(token):
    url = "http://localhost:8000/routers/v1/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Get /me failed: {response.text}"
    result = response.json()
    print("\nGet Me Result:")
    print(json.dumps(result, indent=2))
    for field in ["clerk_id", "email", "name", "picture", "gmail_connected", "gmail_email", "gmail_tokens", "created_at"]:
        assert field in result, f"User response missing {field}"

def test_update_me(token):
    url = "http://localhost:8000/routers/v1/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    update_data = {"name": "Jane Doe", "picture": "https://example.com/new_avatar.jpg"}
    response = requests.patch(url, json=update_data, headers=headers)
    assert response.status_code == 200, f"Update /me failed: {response.text}"
    result = response.json()
    print("\nUpdate Me Result:")
    print(json.dumps(result, indent=2))
    assert result["name"] == "Jane Doe"
    assert result["picture"] == "https://example.com/new_avatar.jpg"

if __name__ == "__main__":
    print("Testing email classification API...")
    test_classify_endpoint()
    print("\nTesting categories endpoint...")
    test_categories_endpoint() 