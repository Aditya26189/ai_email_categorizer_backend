from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse
from loguru import logger

router = APIRouter(tags=["auth-callback"])

@router.get("/auth/callback")
async def auth_callback_redirect(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State parameter for security")
):
    """
    Redirect from /auth/callback to the correct OAuth callback endpoint.
    This handles the frontend's expected callback URL.
    """
    logger.info(f"Redirecting OAuth callback from /auth/callback to /routers/v1/gmail/oauth/callback")
    
    # Redirect to the correct callback endpoint with the same parameters
    redirect_url = f"/routers/v1/gmail/oauth/callback?code={code}&state={state}"
    return RedirectResponse(url=redirect_url, status_code=302) 