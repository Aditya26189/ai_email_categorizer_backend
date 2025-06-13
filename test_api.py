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

if __name__ == "__main__":
    print("Testing email classification API...")
    test_classify_endpoint() 