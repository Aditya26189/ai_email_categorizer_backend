from storage import storage
from datetime import datetime
import textwrap
from typing import Dict

def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp to a more readable format."""
    dt = datetime.fromisoformat(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_email(email: Dict) -> str:
    """Format a single email into a readable string."""
    # Format the timestamp
    timestamp = format_timestamp(email['timestamp'])
    
    # Wrap the body text to 80 characters
    wrapped_body = textwrap.fill(email['body'], width=80)
    
    # Create the formatted output
    output = [
        "=" * 80,
        f"📧 Subject: {email['subject']}",
        f"📅 Time: {timestamp}",
        f"🏷️  Category: {email['category']}",
        "-" * 80,
        "📝 Body:",
        wrapped_body,
        "=" * 80,
        ""  # Empty line for spacing
    ]
    
    return "\n".join(output)

def display_emails():
    """Display all emails in a readable format."""
    print("\n📬 Displaying All Emails (Most Recent First)\n")
    
    try:
        # Get all emails
        emails = storage.get_all_emails()
        
        if not emails:
            print("No emails found in the database.")
            return
        
        # Display email count
        print(f"Found {len(emails)} emails:\n")
        
        # Display each email
        for email in emails:
            print(format_email(email))
            
    except Exception as e:
        print(f"❌ Error displaying emails: {str(e)}")
    finally:
        # Always close the connection
        storage.close()

if __name__ == "__main__":
    display_emails() 