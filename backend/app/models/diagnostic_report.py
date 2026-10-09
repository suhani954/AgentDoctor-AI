from datetime import datetime, timezone
from typing import Any


def diagnostic_report_document(
    *,
    user_id: str,
    agent_id: str,
    agent_name: str,
    report_type: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "agent_id": agent_id,
        "agent_name": agent_name,
        "report_type": report_type,
        "payload": payload,
        "created_at": datetime.now(timezone.utc),
    }


def serialize_diagnostic_report(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "user_id": document["user_id"],
        "agent_id": document["agent_id"],
        "agent_name": document["agent_name"],
        "report_type": document["report_type"],
        "payload": document["payload"],
        "created_at": document["created_at"],
    }
