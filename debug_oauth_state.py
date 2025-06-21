#!/usr/bin/env python3
"""
Debug script to help identify OAuth state validation issues
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def debug_oauth_state():
    """Debug OAuth state generation and validation"""
    print("🔍 Debugging OAuth State Validation...")
    
    try:
        from app.services.google_oauth import google_oauth_service
        print("✅ Successfully imported google_oauth_service")
        
        # Test state generation
        print("\n🧪 Testing state generation...")
        auth_url, state = google_oauth_service.generate_auth_url()
        print(f"Generated state: {state}")
        print(f"State length: {len(state)}")
        print(f"State type: {type(state)}")
        
        # Test state format
        if state and len(state) > 10:
            print("✅ State appears to be properly generated")
        else:
            print("❌ State generation issue detected")
            
        # Test OAuth flow creation
        print("\n🧪 Testing OAuth flow creation...")
        flow = google_oauth_service.create_oauth_flow()
        print(f"Flow created successfully: {flow is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during OAuth state debugging: {e}")
        return False

def check_backend_endpoints():
    """Check if backend endpoints are working correctly"""
    print("\n🔍 Checking backend endpoints...")
    
    try:
        # Check if the OAuth start endpoint exists
        with open('app/routers/gmail.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ("OAuth start endpoint", "async def start_oauth_flow"),
            ("State generation", "generate_auth_url"),
            ("State parameter", "state"),
            ("Auth URL generation", "auth_url"),
        ]
        
        all_passed = True
        for check_name, check_text in checks:
            if check_text in content:
                print(f"✅ {check_name}: Found")
            else:
                print(f"❌ {check_name}: Missing")
                all_passed = False
                
        return all_passed
        
    except Exception as e:
        print(f"❌ Error checking backend endpoints: {e}")
        return False

def main():
    """Main debug function"""
    print("🔍 OAuth State Validation Debug Tool\n")
    
    # Test OAuth state generation
    if not asyncio.run(debug_oauth_state()):
        print("\n❌ OAuth state debugging failed")
        return False
    
    # Check backend endpoints
    if not check_backend_endpoints():
        print("\n❌ Backend endpoint check failed")
        return False
    
    print("\n🎉 Debug checks completed!")
    print("\n📝 Common causes of 'invalid auth state' errors:")
    print("1. State not being stored in localStorage before redirect")
    print("2. State being cleared before callback processing")
    print("3. Multiple OAuth flows running simultaneously")
    print("4. Browser storage issues (incognito mode, etc.)")
    print("5. State encoding/decoding issues")
    
    print("\n🔧 Debugging steps for frontend:")
    print("1. Add console.log to see state values:")
    print("   console.log('Generated state:', state);")
    print("   console.log('Stored state:', localStorage.getItem('gmail_oauth_state'));")
    print("   console.log('URL state:', new URLSearchParams(window.location.search).get('state'));")
    
    print("\n2. Check if localStorage is working:")
    print("   localStorage.setItem('test', 'value');")
    print("   console.log('Test value:', localStorage.getItem('test'));")
    
    print("\n3. Verify OAuth flow timing:")
    print("   - State should be stored BEFORE redirect")
    print("   - State should be validated IMMEDIATELY on callback")
    print("   - State should be cleared AFTER validation")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 