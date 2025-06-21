#!/usr/bin/env python3
"""
Test script to verify OAuth state logging works correctly
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_oauth_logging():
    """Test OAuth state generation and logging"""
    print("🧪 Testing OAuth state logging...")
    
    try:
        from app.services.google_oauth import google_oauth_service
        print("✅ Successfully imported google_oauth_service")
        
        # Test state generation and storage
        print("\n🧪 Testing state generation and storage...")
        auth_url, state = google_oauth_service.generate_auth_url()
        print(f"Generated state: {state}")
        
        # Test state storage
        test_user_id = "test_user_123"
        storage_success = await google_oauth_service.store_oauth_state(state, test_user_id)
        print(f"State storage success: {storage_success}")
        
        # Test state validation
        print("\n🧪 Testing state validation...")
        validation_success = await google_oauth_service.validate_and_clear_oauth_state(state, test_user_id)
        print(f"State validation success: {validation_success}")
        
        # Test with invalid state
        print("\n🧪 Testing invalid state...")
        invalid_validation = await google_oauth_service.validate_and_clear_oauth_state("invalid_state", test_user_id)
        print(f"Invalid state validation: {invalid_validation}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during OAuth logging test: {e}")
        return False

def check_logging_implementation():
    """Check if logging is properly implemented"""
    print("\n🔍 Checking logging implementation...")
    
    try:
        # Check OAuth service
        with open('app/services/google_oauth.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        oauth_checks = [
            ("State generation logging", "Generated State Details:"),
            ("State validation logging", "Received State Details:"),
            ("State storage logging", "OAuth state stored for user:"),
            ("State comparison logging", "State validation successful:"),
            ("Error logging", "State validation failed:"),
        ]
        
        all_passed = True
        for check_name, check_text in oauth_checks:
            if check_text in content:
                print(f"✅ {check_name}: Found")
            else:
                print(f"❌ {check_name}: Missing")
                all_passed = False
        
        # Check Gmail router
        with open('app/routers/gmail.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        router_checks = [
            ("OAuth start logging", "Starting OAuth flow for user:"),
            ("OAuth callback logging", "Processing OAuth callback (POST) for user:"),
            ("State parameter logging", "State parameter:"),
            ("Error logging", "Error handling OAuth callback"),
        ]
        
        for check_name, check_text in router_checks:
            if check_text in content:
                print(f"✅ {check_name}: Found")
            else:
                print(f"❌ {check_name}: Missing")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error checking logging implementation: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 OAuth State Logging Test\n")
    
    # Test OAuth logging
    if not asyncio.run(test_oauth_logging()):
        print("\n❌ OAuth logging test failed")
        return False
    
    # Check logging implementation
    if not check_logging_implementation():
        print("\n❌ Logging implementation check failed")
        return False
    
    print("\n🎉 All tests passed!")
    print("\n📝 What the logs will show:")
    print("1. State generation with details (length, type, etc.)")
    print("2. State storage confirmation")
    print("3. State validation with comparison")
    print("4. Error details if validation fails")
    print("5. Complete OAuth flow tracking")
    
    print("\n🚀 Next steps:")
    print("1. Start your FastAPI server")
    print("2. Run the OAuth flow")
    print("3. Check the logs for detailed state comparison")
    print("4. Look for any mismatches or issues")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 