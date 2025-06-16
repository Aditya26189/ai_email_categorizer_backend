import requests
import json

def test_classify_endpoint():
    # API endpoint URL
    url = "http://localhost:8000/classify"
    
    # Sample email data
    data = {
        "subject": "Meeting Request: Project Kickoff",
        "body": """
        Hi Team,
        
        I hope this email finds you well. I'd like to schedule a meeting to discuss the kickoff of our new project.
        Please let me know your availability for next week.
        
        Best regards,
        John
        """
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
                assert "subject" in email, "Each email should have a subject"
                assert "category" in email, "Each email should have a category"
                assert "timestamp" in email, "Each email should have a timestamp"
        
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

if __name__ == "__main__":
    print("Testing email classification API...")
    test_classify_endpoint()
    print("\nTesting categories endpoint...")
    test_categories_endpoint() 