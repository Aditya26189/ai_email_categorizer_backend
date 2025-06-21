#!/usr/bin/env python3
"""
Debug script to test authentication and Gmail endpoints
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
CLERK_TOKEN = "YOUR_CLERK_JWT_TOKEN_HERE"  # Replace with your actual token

def test_endpoint(endpoint, method="GET", data=None):
    """Test an endpoint with authentication"""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {CLERK_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data or {})
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        print(f"\n🔍 Testing: {method} {endpoint}")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success!")
            try:
                result = response.json()
                print(f"📄 Response: {json.dumps(result, indent=2)}")
            except:
                print(f"📄 Response: {response.text}")
        elif response.status_code == 403:
            print("❌ 403 Forbidden - Authentication failed!")
            print("💡 Check your Clerk JWT token")
        elif response.status_code == 401:
            print("❌ 401 Unauthorized - Invalid token!")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def main():
    print("🔐 Authentication & Gmail Endpoints Debug")
    print("=" * 50)
    
    if CLERK_TOKEN == "YOUR_CLERK_JWT_TOKEN_HERE":
        print("❌ Please replace CLERK_TOKEN with your actual Clerk JWT token")
        print("💡 Get it from your frontend: console.log(await auth.getToken())")
        return
    
    # Test authentication first
    print("\n1️⃣ Testing Authentication...")
    test_endpoint("/routers/v1/me")
    
    # Test Gmail status
    print("\n2️⃣ Testing Gmail Status...")
    test_endpoint("/routers/v1/gmail/oauth/status")
    
    # Test Gmail watch setup
    print("\n3️⃣ Testing Gmail Watch Setup...")
    test_endpoint("/routers/v1/gmail/watch/setup", method="POST")
    
    # Test other Gmail endpoints
    print("\n4️⃣ Testing Other Gmail Endpoints...")
    test_endpoint("/routers/v1/gmail/oauth/url")
    
    print("\n" + "=" * 50)
    print("🎯 Debug Complete!")
    print("\n💡 If you get 403 errors:")
    print("   - Check your Clerk JWT token is valid")
    print("   - Make sure token is not expired")
    print("   - Verify Authorization header format")

if __name__ == "__main__":
    main() 