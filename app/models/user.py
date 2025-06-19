from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserInDB(BaseModel):
    clerk_user_id: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    image_url: Optional[str] = None
    username: Optional[str] = None
    public_metadata: Dict[str, Any] = Field(default_factory=dict)
    phone_numbers: List[str] = Field(default_factory=list)
    password_enabled: Optional[bool] = None
    last_sign_in: Optional[int] = None
    updated_at: datetime
    created_at: datetime
    gmail_connected: bool = False 