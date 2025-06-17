from fastapi import APIRouter, Request, HTTPException, Depends, Form
from starlette.responses import RedirectResponse
from starlette import status
from loguru import logger
from typing import Annotated
from datetime import timedelta

from app.core.oauth import oauth_client
from app.core.config import settings
from app.db.user_db import user_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    token_expired,
    authenticate_user,
    bcrypt_context,
    user_dependency
)
from app.models.schemas import Token, RefreshTokenRequest, CreateUserRequest
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

# --------------------
# Google OAuth Routes
# --------------------

@router.get("/auth/google/login")
async def login(request: Request):
    """Start Google OAuth flow."""
    try:
        logger.info("Starting Google OAuth login")
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        return await oauth_client.google.authorize_redirect(request, redirect_uri)
    except Exception as e:
        logger.error(f"OAuth login error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/auth/callback")
async def auth_callback(request: Request):
    """Google OAuth callback handler."""
    try:
        logger.info("Handling Google OAuth callback")
        token = await oauth_client.google.authorize_access_token(request)
        user_info = await oauth_client.google.userinfo(token=token)

        logger.info(f"OAuth user: {user_info}")

        # Store or update user in MongoDB
        email = user_info.get("email")
        existing_user = await user_db.get_user_by_email(email)

        if not existing_user:
            await user_db.create_user({
                "email": email,
                "name": user_info.get("name"),
                "picture": user_info.get("picture")
            })

        request.session['user'] = {
            'email': email,
            'name': user_info.get("name"),
            'picture': user_info.get("picture")
        }

        return RedirectResponse(url=settings.FRONTEND_URL)

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/auth/google/logout")
async def logout(request: Request):
    """Clear user session."""
    request.session.pop('user', None)
    return RedirectResponse(url=settings.FRONTEND_URL)


# -----------------------
# Traditional Auth Routes
# -----------------------

@router.post("/create-user", status_code=status.HTTP_201_CREATED)
async def create_user(create_user_request: CreateUserRequest):
    user_data = {
        "email": create_user_request.username,
        "username": create_user_request.username,
        "hashed_password": bcrypt_context.hash(create_user_request.password),
        "created_at": settings.now_utc().isoformat()
    }

    # Check if user already exists
    existing_user = await user_db.get_user_by_email(create_user_request.username)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    # Try to create user
    success = await user_db.create_user(user_data)
    if success is False:  # Explicitly check for False
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    return {"message": "User created successfully"}


@router.get("/get-user")
async def get_user(user: user_dependency):
    return user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    db = user_db.collection
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(user["username"], str(user["_id"]), timedelta(days=7))
    refresh_token = create_refresh_token(user["username"], str(user["_id"]), timedelta(days=14))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token_request: RefreshTokenRequest):
    token = refresh_token_request.refresh_token

    if token_expired(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user = decode_token(token)
    access_token = create_access_token(user["sub"], user["id"], timedelta(days=7))
    refresh_token = create_refresh_token(user["sub"], user["id"], timedelta(days=14))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
