from typing import Annotated, Dict
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from loguru import logger

# API Key header for authentication
api_key_header = APIKeyHeader(name="X-API-Key")

# In production, this would be in a database
API_KEYS: Dict[str, dict] = {
    "cust_companyA_123456": {
        "name": "Company A",
        "plan": "premium",
        "rate_limit": 1000  # requests per day
    },
    "cust_companyB_789012": {
        "name": "Company B",
        "plan": "basic",
        "rate_limit": 100  # requests per day
    }
}

async def get_api_key(api_key: Annotated[str, Depends(api_key_header)]) -> dict:
    """Validate API key and return customer info."""
    if api_key not in API_KEYS:
        logger.warning(f"Invalid API key attempt: {api_key[:4]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    
    customer = API_KEYS[api_key]
    logger.info(f"API access by {customer['name']} ({customer['plan']} plan)")
    return customer

# Common dependencies
APIKey = Annotated[dict, Depends(get_api_key)] 