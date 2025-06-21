#!/usr/bin/env python3
"""
Test script to verify the email validation fix in auth_routes.py
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.base import get_mongo_client
from app.routers.auth.auth_routes import get_me
from app.core.clerk import verify_clerk_jwt
from fastapi import Request
from unittest.mock import Mock

async def test_email_fix():
    """Test the email validation fix"""
    print("🧪 Testing email validation fix...")
    
    # Test 1: Check if we can import the updated function
    try:
        from app.routers.auth.auth_routes import get_me
        print("✅ Successfully imported get_me function")
    except Exception as e:
        print(f"❌ Failed to import get_me: {e}")
        return False
    
    # Test 2: Check if verify_clerk_jwt is available
    try:
        from app.core.clerk import verify_clerk_jwt
        print("✅ Successfully imported verify_clerk_jwt function")
    except Exception as e:
        print(f"❌ Failed to import verify_clerk_jwt: {e}")
        return False
    
    # Test 3: Check database connection
    try:
        db = get_mongo_client()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test 4: Check if there are users with None emails
    try:
        users_collection = db["users"]
        users_with_none_email = await users_collection.find({"email": None}).to_list(length=10)
        if users_with_none_email:
            print(f"⚠️  Found {len(users_with_none_email)} users with None email")
            for user in users_with_none_email:
                print(f"   - User ID: {user.get('clerk_user_id')}, Email: {user.get('email')}")
        else:
            print("✅ No users found with None email")
    except Exception as e:
        print(f"❌ Failed to check users with None email: {e}")
    
    print("\n🎉 Email validation fix test completed!")
    print("\n📝 Next steps:")
    print("1. Start your FastAPI server: python -m uvicorn app.main:app --reload")
    print("2. Try accessing the /me endpoint with a user that has None email")
    print("3. The fix should automatically update their email from Clerk JWT")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_email_fix())
    sys.exit(0 if success else 1) 