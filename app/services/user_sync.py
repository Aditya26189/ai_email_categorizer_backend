from app.db.base import get_mongo_client
from app.models.user import UserInDB
from datetime import datetime

async def create_user_from_clerk(data: dict):
    # Find primary email address
    email = None
    email_addresses = data.get("email_addresses", [])
    primary_email_id = data.get("primary_email_address_id")
    for e in email_addresses:
        if e.get("id") == primary_email_id:
            email = e.get("email_address")
            break
    if not email and email_addresses:
        email = email_addresses[0].get("email_address")

    user = UserInDB(
        clerk_user_id=data["id"],
        email=email,
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        image_url=data.get("image_url"),
        username=data.get("username"),
        public_metadata=data.get("public_metadata", {}),
        phone_numbers=data.get("phone_numbers", []),
        password_enabled=data.get("password_enabled"),
        last_sign_in=data.get("last_sign_in_at"),
        updated_at=datetime.fromtimestamp(data["updated_at"] / 1000),
        created_at=datetime.fromtimestamp(data["created_at"] / 1000),
        gmail_connected=False
    )

    db = get_mongo_client()
    await db["users"].insert_one(user.model_dump())

async def update_user_from_clerk(data: dict):
    # Find primary email address
    email = None
    email_addresses = data.get("email_addresses", [])
    primary_email_id = data.get("primary_email_address_id")
    for e in email_addresses:
        if e.get("id") == primary_email_id:
            email = e.get("email_address")
            break
    if not email and email_addresses:
        email = email_addresses[0].get("email_address")

    db = get_mongo_client()
    await db["users"].update_one(
        {"clerk_user_id": data["id"]},
        {
            "$set": {
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "image_url": data.get("image_url"),
                "username": data.get("username"),
                "email": email,
                "public_metadata": data.get("public_metadata", {}),
                "phone_numbers": data.get("phone_numbers", []),
                "password_enabled": data.get("password_enabled"),
                "last_sign_in": data.get("last_sign_in_at"),
                "updated_at": datetime.fromtimestamp(data["updated_at"] / 1000),
            }
        },
        upsert=False
    ) 