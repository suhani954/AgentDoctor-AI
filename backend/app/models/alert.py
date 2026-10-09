from datetime import datetime, timezone
from typing import Any


def alert_document(
    *,
    user_id: str,
    agent_id: str,
    agent_name: str,
    title: str,
    severity: str,
    message: str,
    source: str,
) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "agent_id": agent_id,
        "agent_name": agent_name,
        "title": title,
        "severity": severity,
        "message": message,
        "source": source,
        "is_read": False,
        "created_at": datetime.now(timezone.utc),
    }


def serialize_alert(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "user_id": document["user_id"],
        "agent_id": document["agent_id"],
        "agent_name": document["agent_name"],
        "title": document["title"],
        "severity": document["severity"],
        "message": document["message"],
        "source": document["source"],
        "is_read": document.get("is_read", False),
        "created_at": document["created_at"],
    }