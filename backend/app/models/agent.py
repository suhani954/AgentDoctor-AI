from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def agent_document(
    *,
    user_id: str,
    name: str,
    description: str | None,
    model: str,
    status: str,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "name": name,
        "description": description,
        "model": model,
        "status": status,
        "created_at": now,
        "updated_at": now,
    }


def serialize_agent(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "user_id": document["user_id"],
        "name": document["name"],
        "description": document.get("description"),
        "model": document["model"],
        "status": document.get("status", "active"),
        "created_at": document.get("created_at"),
        "updated_at": document.get("updated_at"),
    }


def object_id_from_string(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise ValueError("Invalid agent id")
    return ObjectId(value)