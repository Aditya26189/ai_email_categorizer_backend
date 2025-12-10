#!/usr/bin/env python3
"""
Test script for email re-categorization functionality.
This script demonstrates how to use the new re-categorization endpoints.
"""

import requests
import json
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
AUTH_TOKEN = "YOUR_AUTH_TOKEN_HERE"  # Replace with actual token

class EmailRecategorizationTester:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        }
    
    def recategorize_single_email(self, gmail_id: str, new_category: Optional[str] = None, regenerate_summary: bool = False):
        """
        Re-categorize a single email.
        
        Args:
            gmail_id: Gmail ID of the email to recategorize
            new_category: New category (if None, AI will re-classify)
            regenerate_summary: Whether to regenerate the summary
        """
        url = f"{self.base_url}/routers/v1/emails/recategorize"
        
        payload = {
            "gmail_id": gmail_id,
            "regenerate_summary": regenerate_summary
        }
        
        if new_category:
            payload["new_category"] = new_category
        
        try:
            response = requests.put(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            print("✅ Single Email Recategorization Success:")
            print(f"   Gmail ID: {result['gmail_id']}")
            print(f"   {result['old_category']} → {result['new_category']}")
            
            if result.get('summary'):
                print(f"   Summary regenerated: {len(result['summary'])} bullet points")
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error recategorizing email: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")
            return None
    
    def bulk_recategorize_emails(self, category_filter: Optional[str] = None, regenerate_summary: bool = False):
        """
        Bulk re-categorize emails.
        
        Args:
            category_filter: Filter by current category (if None, processes all emails)
            regenerate_summary: Whether to regenerate summaries
        """
        url = f"{self.base_url}/routers/v1/emails/recategorize/bulk"
        
        params = {
            "regenerate_summary": regenerate_summary
        }
        
        if category_filter:
            params["category"] = category_filter
        
        try:
            response = requests.put(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            print("✅ Bulk Recategorization Success:")
            print(f"   Total processed: {result['total_processed']}")
            print(f"   Successful: {result['successful']}")
            print(f"   Failed: {result['failed']}")
            
            if category_filter:
                print(f"   Category filter: {category_filter}")
                
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error in bulk recategorization: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")
            return None
    
    def get_emails_by_category(self, category: str, limit: int = 5):
        """Get emails by category to find Gmail IDs for testing."""
        url = f"{self.base_url}/routers/v1/emails/emails"
        params = {
            "category": category,
            "limit": limit
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            emails = response.json()
            print(f"📧 Found {len(emails)} emails in '{category}' category:")
            
            for email in emails:
                print(f"   ID: {email['gmail_id']} | Subject: {email['subject'][:50]}...")
            
            return emails
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching emails: {e}")
            return []

def main():
    """Main function to demonstrate re-categorization functionality."""
    print("🤖 Email Re-categorization Test Script")
    print("=====================================\n")
    
    # Initialize tester
    tester = EmailRecategorizationTester(BASE_URL, AUTH_TOKEN)
    
    print("Note: Make sure to replace AUTH_TOKEN with your actual authentication token\n")
    
    # Example 1: Get some emails to work with
    print("1. Getting emails from 'Personal' category...")
    personal_emails = tester.get_emails_by_category("Personal", limit=2)
    
    if personal_emails:
        # Example 2: Re-categorize single email with manual category
        gmail_id = personal_emails[0]['gmail_id']
        print(f"\n2. Re-categorizing email {gmail_id} to 'Work' category...")
        tester.recategorize_single_email(
            gmail_id=gmail_id,
            new_category="Work",
            regenerate_summary=True
        )
        
        # Example 3: Let AI re-classify another email
        if len(personal_emails) > 1:
            gmail_id_2 = personal_emails[1]['gmail_id']
            print(f"\n3. Letting AI re-classify email {gmail_id_2}...")
            tester.recategorize_single_email(
                gmail_id=gmail_id_2,
                regenerate_summary=False
            )
    
    # Example 4: Bulk re-categorization of specific category
    print("\n4. Bulk re-categorizing all 'Shopping' emails...")
    tester.bulk_recategorize_emails(
        category_filter="Shopping",
        regenerate_summary=False
    )
    
    # Example 5: Bulk re-categorization of all emails (commented out for safety)
    print("\n5. Bulk re-categorization of ALL emails (uncomment to test)...")
    print("   # Uncomment the line below to test bulk processing of all emails")
    print("   # tester.bulk_recategorize_emails(regenerate_summary=False)")
    
    print("\n✅ Test script completed!")
    print("\nNext steps:")
    print("1. Replace AUTH_TOKEN with your actual token")
    print("2. Ensure the server is running on localhost:8000")
    print("3. Run this script to test the re-categorization functionality")

if __name__ == "__main__":
    main()
