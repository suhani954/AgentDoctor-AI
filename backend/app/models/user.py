from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def user_document(
    *,
    name: str,
    email: str,
    hashed_password: str,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "name": name,
        "email": email.lower(),
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }


def serialize_user(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "name": document["name"],
        "email": document["email"],
        "is_active": document.get("is_active", True),
        "created_at": document.get("created_at"),
        "updated_at": document.get("updated_at"),
    }


def object_id_from_string(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise ValueError("Invalid user id")
    return ObjectId(value)
