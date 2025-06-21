import requests
import os
import sys

API_URL = os.environ.get("API_URL", "http://localhost:8000/routers/v1/auth/me")
JWT = os.environ.get("CLERK_JWT") or (sys.argv[1] if len(sys.argv) > 1 else None)

if not JWT:
    print("❌ Please provide a Clerk JWT via the CLERK_JWT environment variable or as a command line argument.")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {JWT}"
}

print(f"🔗 Calling {API_URL} with provided JWT...")
response = requests.get(API_URL, headers=headers)

print(f"Status code: {response.status_code}")
try:
    data = response.json()
except Exception:
    print("❌ Could not parse JSON response:", response.text)
    sys.exit(1)

print("Response:", data)

email = data.get("email")
if email and "@" in email:
    print(f"✅ User email is valid: {email}")
else:
    print(f"❌ User email is invalid or missing: {email}")
    sys.exit(1)

print("\n🎉 /me endpoint integration test passed!") 