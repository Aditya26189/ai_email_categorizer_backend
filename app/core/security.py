from fastapi import APIRouter, Depends, HTTPException
from datetime import timedelta, datetime, UTC
from typing import Annotated
from starlette import status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from authlib.integrations.starlette_client import OAuth
from jose import jwt, JWTError
from starlette.config import Config

from ..models.schemas import GoogleUser
from ..db.base import db as mongo_db
from .config import settings
from .oauth import oauth
from bson.objectid import ObjectId

# Authentication settings
ALGORITHM = "HS256"
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

# ---------------------------
# Authentication Functions
# ---------------------------

async def authenticate_user(username: str, password: str, db):
    user = await db.find_one({"username": username})
    if not user:
        return False
    if not bcrypt_context.verify(password, user.get("hashed_password", "")):
        return False
    return user


def create_access_token(username: str, user_id: str, expires_delta: timedelta):
    payload = {"sub": username, "id": str(user_id)}
    expires = datetime.now(UTC) + expires_delta
    payload.update({"exp": expires})
    return jwt.encode(payload, settings.SESSION_SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(username: str, user_id: str, expires_delta: timedelta):
    return create_access_token(username, user_id, expires_delta)


def decode_token(token: str):
    return jwt.decode(token, settings.SESSION_SECRET_KEY, algorithms=[ALGORITHM])


async def get_current_user(token: Annotated[str, Depends(oauth_bearer)]):
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        user_id = payload.get("id")

        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")

        db = mongo_db.get_db()
        user = await db["users"].find_one({"_id": ObjectId(user_id)})

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

        user.pop("hashed_password", None)
        return user

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid")


def token_expired(token: Annotated[str, Depends(oauth_bearer)]):
    try:
        payload = decode_token(token)
        return datetime.fromtimestamp(payload.get("exp"), UTC) <= datetime.now(UTC)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate token")


async def get_user_by_google_sub(google_sub: str):
    db = mongo_db.get_db()
    return await db["users"].find_one({"google_sub": google_sub})


async def create_user_from_google_info(google_user: GoogleUser):
    db = mongo_db.get_db()
    email = google_user.email
    google_sub = google_user.sub

    existing_user = await db["users"].find_one({"email": email})

    if existing_user:
        await db["users"].update_one(
            {"_id": existing_user["_id"]},
            {"$set": {"google_sub": google_sub}}
        )
        return await db["users"].find_one({"_id": existing_user["_id"]})
    else:
        new_user = {
            "username": email,
            "email": email,
            "google_sub": google_sub,
            "created_at": datetime.utcnow().isoformat()
        }
        result = await db["users"].insert_one(new_user)
        return await db["users"].find_one({"_id": result.inserted_id})


user_dependency = Annotated[dict, Depends(get_current_user)]
