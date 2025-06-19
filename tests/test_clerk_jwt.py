import os
import httpx
from dotenv import load_dotenv

load_dotenv()

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_API_BASE = "https://api.clerk.dev/v1"
USER_ID = "user_2ygYPzJWTNMDyyCVV3Rk31U89oV"  

headers = {
    "Authorization": f"Bearer {CLERK_SECRET_KEY}",
    "Content-Type": "application/json"
}

def create_session_and_get_jwt(user_id: str):
    create_session_url = f"{CLERK_API_BASE}/sessions"
    payload = {"user_id": user_id}

    with httpx.Client() as client:
        # Create a new session
        resp = client.post(create_session_url, headers=headers, json=payload)
        if resp.status_code != 200:
            print("❌ Failed to create session")
            print(resp.text)
            return None

        session_id = resp.json().get("id")
        print(f"✅ Session created: {session_id}")

        # Now get JWT for that session
        token_url = f"{CLERK_API_BASE}/sessions/{session_id}/tokens"
        token_resp = client.post(token_url, headers=headers)

        if token_resp.status_code != 200:
            print("❌ Failed to fetch JWT")
            print(token_resp.text)
            return None

        jwt = token_resp.json().get("jwt")
        print("✅ JWT token retrieved:")
        print(jwt)
        return jwt

if __name__ == "__main__":
    if not CLERK_SECRET_KEY or not USER_ID:
        print("❌ Missing environment variables. Add CLERK_SECRET_KEY and TEST_USER_ID in .env")
    else:
        create_session_and_get_jwt(USER_ID)
