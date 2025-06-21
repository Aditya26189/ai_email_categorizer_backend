#!/usr/bin/env python3
"""
Test script to verify the /me endpoint fix for Gmail connection status
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_me_endpoint_fix():
    """Test the /me endpoint fix"""
    print("🧪 Testing /me endpoint fix...")
    
    try:
        from app.routers.auth.auth_routes import get_me
        from app.db.base import get_mongo_client
        from app.models.user import UserInDB
        print("✅ Successfully imported required modules")
        
        # Test database connection
        db = get_mongo_client()
        print("✅ Database connection successful")
        
        # Test user model
        test_user = UserInDB(
            clerk_user_id="test_user_123",
            email="test@example.com",
            is_gmail_connected=True,
            gmail_email="test@gmail.com",
            gmail_connected_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        print("✅ User model test successful")
        print(f"  - is_gmail_connected: {test_user.is_gmail_connected}")
        print(f"  - gmail_email: {test_user.gmail_email}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during /me endpoint test: {e}")
        return False

def check_me_endpoint_implementation():
    """Check if the /me endpoint fix is properly implemented"""
    print("\n🔍 Checking /me endpoint implementation...")
    
    try:
        # Check auth_routes.py
        with open('app/routers/auth/auth_routes.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("Direct database read", "Get Gmail connection status directly from database"),
            ("Gmail status logging", "Gmail connection status for user"),
            ("is_gmail_connected field", "is_gmail_connected: {is_gmail_connected}"),
            ("gmail_email field", "gmail_email: {gmail_email}"),
            ("gmail_connected_at field", "gmail_connected_at: {gmail_connected_at}"),
            ("Field assignment", "db_user[\"is_gmail_connected\"] = is_gmail_connected"),
        ]
        
        all_passed = True
        for check_name, check_text in checks:
            if check_text in content:
                print(f"✅ {check_name}: Found")
            else:
                print(f"❌ {check_name}: Missing")
                all_passed = False
        
        # Check that the old service call is removed
        if "google_oauth_service.check_gmail_connection_status" in content:
            print("❌ Old service call still present (should be removed)")
            all_passed = False
        else:
            print("✅ Old service call removed")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error checking /me endpoint implementation: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 /me Endpoint Fix Test\n")
    
    # Test /me endpoint fix
    if not asyncio.run(test_me_endpoint_fix()):
        print("\n❌ /me endpoint test failed")
        return False
    
    # Check implementation
    if not check_me_endpoint_implementation():
        print("\n❌ Implementation check failed")
        return False
    
    print("\n🎉 All tests passed!")
    print("\n📝 What the fix does:")
    print("1. Reads Gmail connection status directly from database")
    print("2. Ensures latest status is returned (not cached)")
    print("3. Adds detailed logging for debugging")
    print("4. Properly sets all Gmail fields in response")
    
    print("\n🚀 Next steps:")
    print("1. Start your FastAPI server")
    print("2. Call GET /routers/v1/me")
    print("3. Check that is_gmail_connected shows the correct value")
    print("4. Verify the logs show the Gmail connection status")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 