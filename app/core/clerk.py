from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import jwt, jwk
import requests
from app.core.config import settings
from loguru import logger
from functools import lru_cache
from app.db.user_db import user_db
from datetime import datetime

security = HTTPBearer()

# Ensure CLERK_ISSUER is a full URL (with https://)
CLERK_ISSUER = settings.CLERK_FRONTEND_API
if not CLERK_ISSUER.startswith("http"):
    CLERK_ISSUER = f"https://{CLERK_ISSUER}"
JWKS_URL = f"{CLERK_ISSUER}/.well-known/jwks.json"
AUDIENCE = settings.FRONTEND_URL  # Set this in your .env or config

@lru_cache(maxsize=1)
def get_jwks():
    return requests.get(JWKS_URL).json()

def get_public_key(token: str):
    jwks = get_jwks()
    header = jwt.get_unverified_header(token)
    for key in jwks["keys"]:
        if key["kid"] == header["kid"]:
            return jwk.construct(key, algorithm="RS256")
    raise Exception("Public key not found")

async def clerk_auth(credentials=Depends(security)):
    token = credentials.credentials
    try:
        key = get_public_key(token)
        payload = jwt.decode(
            token,
            key=key,
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=CLERK_ISSUER,
        )
        logger.info("✅ Clerk JWT verified.")
        # Extract user info from token
        clerk_user_id = payload.get("sub")
        # Always check if user exists in MongoDB by Clerk user ID first
        await user_db.init()
        db_user = await user_db.collection.find_one({"clerk_user_id": clerk_user_id})
        if db_user:
            logger.info(f"User exists in DB (by clerk_user_id): {clerk_user_id}")
            return db_user
        # If not found, extract user info from JWT or Clerk API and create user
        email = payload.get("email") or payload.get("primary_email_address")
        if not email:
            logger.warning(f"JWT payload missing email for Clerk user_id: {clerk_user_id}, payload: {payload}")
            # Try to fetch user from Clerk API
            try:
                if not clerk_user_id or not settings.CLERK_SECRET_KEY:
                    logger.error("Cannot fetch user from Clerk API: missing user_id or Clerk secret key.")
                    raise HTTPException(status_code=400, detail="No email found in Clerk token and cannot fetch from Clerk API.")
                clerk_api_url = f"https://api.clerk.dev/v1/users/{clerk_user_id}"
                resp = requests.get(
                    clerk_api_url,
                    headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"}
                )
                if resp.status_code != 200:
                    logger.error(f"Failed to fetch user from Clerk API: {resp.status_code} {resp.text}")
                    raise HTTPException(status_code=400, detail="Failed to fetch user info from Clerk API.")
                clerk_user = resp.json()
                email = (
                    clerk_user.get("email_address")
                    or clerk_user.get("primary_email_address")
                    or (clerk_user["email_addresses"][0]["email_address"] if clerk_user.get("email_addresses") and len(clerk_user["email_addresses"]) > 0 else None)
                )
                if email:
                    logger.info(f"Fetched user from Clerk API: {email}")
                else:
                    logger.error(f"Clerk API user info missing email: {clerk_user}")
                    raise HTTPException(status_code=400, detail="No email found in Clerk user info.")
                name = clerk_user.get("full_name")
                picture = clerk_user.get("image_url")
            except Exception as api_e:
                logger.error(f"Error fetching user from Clerk API: {api_e}")
                raise HTTPException(status_code=400, detail="No email found in Clerk token and failed to fetch from Clerk API.")
        else:
            name = payload.get("full_name")
            picture = payload.get("image_url")
        logger.info(f"Creating new user in DB: {email}")
        user_data = {
            "email": email,
            "username": email,
            "name": name,
            "picture": picture,
            "created_at": datetime.utcnow(),
            "clerk_user_id": clerk_user_id
        }
        await user_db.create_user(user_data)
        db_user = await user_db.collection.find_one({"clerk_user_id": clerk_user_id})
        logger.info(f"New user created: {email}")
        return db_user
    except Exception as e:
        logger.error(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authentication Credentials",
        )
