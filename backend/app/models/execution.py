from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def execution_document(
    *,
    user_id: str,
    agent_id: str,
    input: str,
    output: str | None,
    status: str,
    error_message: str | None,
    latency_ms: int,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cost: float,
    tool_calls: list[dict[str, Any]],
    trace_steps: list[dict[str, Any]],
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "agent_id": agent_id,
        "input": input,
        "output": output,
        "status": status,
        "error_message": error_message,
        "latency_ms": latency_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost": cost,
        "tool_calls": tool_calls,
        "trace_steps": trace_steps,
        "created_at": now,
    }


def serialize_execution(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "user_id": document["user_id"],
        "agent_id": document["agent_id"],
        "input": document["input"],
        "output": document.get("output"),
        "status": document["status"],
        "error_message": document.get("error_message"),
        "latency_ms": document.get("latency_ms", 0),
        "prompt_tokens": document.get("prompt_tokens", 0),
        "completion_tokens": document.get("completion_tokens", 0),
        "total_tokens": document.get("total_tokens", 0),
        "cost": document.get("cost", 0),
        "tool_calls": document.get("tool_calls", []),
        "trace_steps": document.get("trace_steps", []),
        "created_at": document.get("created_at"),
    }


def object_id_from_string(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise ValueError("Invalid execution id")
    return ObjectId(value)