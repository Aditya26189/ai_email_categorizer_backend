from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import jwt, jwk
import requests
from app.core.config import settings
from loguru import logger
from functools import lru_cache
from datetime import datetime
from app.db.base import get_mongo_client

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
        if not clerk_user_id:
            logger.error("No Clerk user ID (sub) in JWT.")
            raise HTTPException(status_code=400, detail="No Clerk user ID found in token.")
        db = get_mongo_client()
        db_user = await db["users"].find_one({"clerk_user_id": clerk_user_id})
        if db_user:
            logger.info(f"User exists in DB (by clerk_user_id): {clerk_user_id}")
            return db_user
        # If not found, create minimal user record
        email = payload.get("email")
        user_data = {
            "clerk_user_id": clerk_user_id,
            "email": email
        }
        await db["users"].insert_one(user_data)
        db_user = await db["users"].find_one({"clerk_user_id": clerk_user_id})
        logger.info(f"New user created: {clerk_user_id}")
        return db_user
    except Exception as e:
        logger.error(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authentication Credentials",
        )

async def verify_clerk_jwt(token: str):
    try:
        key = get_public_key(token)
        payload = jwt.decode(
            token,
            key=key,
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=CLERK_ISSUER,
        )
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Authentication Credentials: {e}",
        )
