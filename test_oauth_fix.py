#!/usr/bin/env python3
"""
Test script to verify the OAuth callback fix
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_oauth_imports():
    """Test if the OAuth service can be imported without errors"""
    print("🧪 Testing OAuth service imports...")
    
    try:
        from app.services.google_oauth import google_oauth_service
        print("✅ Successfully imported google_oauth_service")
    except Exception as e:
        print(f"❌ Failed to import google_oauth_service: {e}")
        return False
    
    try:
        from googleapiclient.discovery import build
        print("✅ Successfully imported googleapiclient.discovery")
    except Exception as e:
        print(f"❌ Failed to import googleapiclient.discovery: {e}")
        return False
    
    return True

def test_code_structure():
    """Test the code structure changes"""
    print("\n🔍 Testing OAuth callback code structure...")
    
    try:
        # Read the google_oauth.py file to check our changes
        with open('app/services/google_oauth.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key changes we made
        checks = [
            ("Google API userinfo call", "service = build('oauth2', 'v2', credentials=credentials)"),
            ("userinfo().get().execute()", "user_info = service.userinfo().get().execute()"),
            ("user_info.get instead of id_info.get", "user_info.get(\"email\")"),
            ("Removed JWT decode", "jwt.decode"),
        ]
        
        all_passed = True
        for check_name, check_text in checks:
            if check_text in content:
                if "Removed JWT decode" in check_name:
                    print(f"❌ {check_name}: Still present (should be removed)")
                    all_passed = False
                else:
                    print(f"✅ {check_name}: Found")
            else:
                if "Removed JWT decode" in check_name:
                    print(f"✅ {check_name}: Successfully removed")
                else:
                    print(f"❌ {check_name}: Missing")
                    all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Failed to read google_oauth.py: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing OAuth callback fix...\n")
    
    # Test imports
    if not asyncio.run(test_oauth_imports()):
        print("\n❌ Import tests failed")
        return False
    
    # Test code structure
    if not test_code_structure():
        print("\n❌ Code structure tests failed")
        return False
    
    print("\n🎉 All tests passed!")
    print("\n📝 Summary of fixes implemented:")
    print("✅ Removed problematic JWT decode call")
    print("✅ Added Google OAuth2 API userinfo call")
    print("✅ Updated all references to use user_info instead of id_info")
    print("✅ Fixed the 'decode() missing 1 required positional argument: key' error")
    
    print("\n🚀 Next steps:")
    print("1. The OAuth callback should now work without JWT decode errors")
    print("2. Try the Gmail OAuth flow again")
    print("3. Check that tokens are properly stored in MongoDB")
    print("4. Verify that user's Gmail connection status is updated")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 