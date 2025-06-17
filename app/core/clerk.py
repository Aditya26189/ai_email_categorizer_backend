from fastapi import Request
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer
from .config import settings
from .logger import log_auth_event, logger

# Configure Clerk
clerk_config = ClerkConfig(
    jwks_url=f"https://{settings.CLERK_FRONTEND_API}.clerk.accounts.dev/.well-known/jwks.json",
    auto_error=True  # Raise errors for missing/invalid tokens
)

# Create Clerk auth middleware
clerk_auth = ClerkHTTPBearer(config=clerk_config, add_state=True)
logger.info("Clerk authentication middleware initialized")

# Helper function to get user info from request
async def get_clerk_user(request: Request):
    """Get the authenticated user's information from the request state."""
    try:
        if not hasattr(request.state, 'clerk_auth'):
            log_auth_event("token_missing")
            return None
        
        decoded = request.state.clerk_auth.decoded
        user_id = decoded.get("sub")
        email = decoded.get("email")
        
        log_auth_event("user_authenticated", user_id=user_id)
        
        return {
            "user_id": user_id,
            "email": email,
            "first_name": decoded.get("first_name"),
            "last_name": decoded.get("last_name")
        }
    except Exception as e:
        log_auth_event("token_verification_failed", error=str(e))
        return None 