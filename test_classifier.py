from classifier import classify_email
from storage import storage

def test_classification_and_storage():
    """
    Test the email classification and storage functionality with a sample email.
    """
    # Sample email
    test_email = {
        "subject": "We would love your feedback on our product for a review article",
        "body": """Hi Aditya, we've seen your work and would love your feedback on our new AI productivity tool. 
        Would you be open to trying it and possibly writing a product review?"""
    }
    
    print("Testing email classification...")
    print(f"Subject: {test_email['subject']}")
    print(f"Body: {test_email['body']}")
    print("\nClassifying email...")
    
    # Classify the email
    category = classify_email(test_email['subject'], test_email['body'])
    print(f"\nClassification result: {category}")
    
    # Add category to the email dictionary
    test_email['category'] = category
    
    print("\nTesting storage...")
    # Save the email
    if storage.save_email(test_email):
        print("Email saved successfully!")
    else:
        print("Email was not saved (possibly a duplicate)")
    
    # Load and verify the saved email
    print("\nVerifying saved email...")
    saved_emails = storage.load_emails()
    found = False
    
    for email in saved_emails:
        if email['subject'] == test_email['subject']:
            found = True
            print("\nFound saved email:")
            print(f"Subject: {email['subject']}")
            print(f"Category: {email['category']}")
            print(f"Timestamp: {email['timestamp']}")
            break
    
    if not found:
        print("Could not find the saved email in storage!")

if __name__ == "__main__":
    test_classification_and_storage() 