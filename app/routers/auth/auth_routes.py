from fastapi import APIRouter, Request, HTTPException, Depends
from loguru import logger
from app.core.clerk import clerk_auth
from app.core.logger import log_request, log_auth_event

router = APIRouter(tags=["auth"])

@router.get("/me")
def get_me(user=Depends(clerk_auth)):
    return {"user": user}
