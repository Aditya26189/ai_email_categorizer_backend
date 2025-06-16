from app.services.storage import storage
from app.services.classifier import classify_email
from datetime import datetime
import asyncio

async def test_mongodb_storage():
    """Test all MongoDB storage functionality."""
    print("\n🔍 Testing MongoDB Storage...")
    
    # Test data
    test_emails = [
        {
            "subject": "Product Review Request",
            "body": "Would you like to review our new AI tool? We'd love your feedback on our latest features."
        },
        {
            "subject": "Meeting Request: Project Discussion",
            "body": "Let's schedule a meeting to discuss the project timeline and deliverables for next week."
        },
        {
            "subject": "Job Offer - Senior Developer Position",
            "body": "We were impressed by your profile and would like to offer you a position as Senior Developer."
        }
    ]
    
    # Test 1: Classify and Save emails
    print("\n📝 Test 1: Classifying and Saving Emails")
    for email in test_emails:
        # Classify the email
        category = classify_email(email['subject'], email['body'])
        if category.startswith("Error:"):
            print(f"❌ Classification failed for '{email['subject']}': {category}")
            continue
            
        # Add category to email
        email['category'] = category
        
        # Save the email
        result = await storage.save_email(email)
        print(f"Saved email '{email['subject']}': {'Success' if result else 'Skipped (duplicate)'}")
    
    # Test 2: Try to save duplicate
    print("\n🔄 Test 2: Duplicate Check")
    duplicate_result = await storage.save_email(test_emails[0])
    print(f"Attempted to save duplicate: {'Skipped (expected)' if not duplicate_result else 'Error: Should have been skipped'}")
    
    # Test 3: Load all emails
    print("\n📥 Test 3: Loading All Emails")
    all_emails = await storage.load_emails()
    print(f"Found {len(all_emails)} emails:")
    for email in all_emails:
        print(f"- {email['subject']} ({email['category']})")
    
    # Test 4: Load limited emails
    print("\n📊 Test 4: Loading Limited Emails")
    limited_emails = await storage.load_emails(limit=2)
    print(f"Found {len(limited_emails)} emails (limited to 2):")
    for email in limited_emails:
        print(f"- {email['subject']}")
    
    # Test 5: Find specific email
    print("\n🔎 Test 5: Finding Specific Email")
    test_subject = "Meeting Request: Project Discussion"
    found_email = await storage.get_email_by_subject(test_subject)
    if found_email:
        print(f"Found email: {found_email['subject']} ({found_email['category']})")
    else:
        print(f"Email with subject '{test_subject}' not found")
    
    # Test 6: Find non-existent email
    print("\n❌ Test 6: Finding Non-existent Email")
    non_existent = await storage.get_email_by_subject("This Email Doesn't Exist")
    print(f"Result for non-existent email: {'Not found (expected)' if non_existent is None else 'Error: Should not have been found'}")

if __name__ == "__main__":
    try:
        asyncio.run(test_mongodb_storage())
    finally:
        # Always close the connection
        asyncio.run(storage.close()) 