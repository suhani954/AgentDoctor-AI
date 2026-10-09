from datetime import datetime, timezone
from typing import Any

from app.db.mongodb import get_database
from app.models.agent import object_id_from_string
from app.schemas.diagnostic_schema import RootCauseAgentResponse, RootCauseEvidence
from app.services.llm_service import ask_ollama_json


AGENT_COLLECTION = "agents"
EXECUTION_COLLECTION = "executions"


def classify_error(error_message: str | None) -> tuple[str, list[str]]:
    if not error_message:
        return (
            "Unknown failure pattern",
            ["Inspect trace steps and tool calls for missing error details."],
        )

    error = error_message.lower()

    if "timeout" in error or "timed out" in error:
        return (
            "Timeout during agent execution",
            [
                "Increase timeout limits for slow tools.",
                "Add retry handling for network or database calls.",
                "Inspect latency-heavy trace steps in the flight recorder.",
            ],
        )

    if "rate limit" in error or "429" in error:
        return (
            "Rate limit exceeded",
            [
                "Add exponential backoff for model and tool calls.",
                "Reduce concurrent requests.",
                "Use request queueing during traffic spikes.",
            ],
        )

    if "database" in error or "mongo" in error or "db" in error:
        return (
            "Database operation failure",
            [
                "Check database connection health.",
                "Add retry logic around database reads and writes.",
                "Review query performance and indexes.",
            ],
        )

    if "tool" in error:
        return (
            "Tool execution failure",
            [
                "Validate tool inputs before execution.",
                "Add error handling around tool calls.",
                "Review failed tool call outputs in the flight recorder.",
            ],
        )

    if "token" in error or "context" in error:
        return (
            "Token or context length issue",
            [
                "Shorten prompts and retrieved context.",
                "Add summarization before long-context model calls.",
                "Use a model with a larger context window when necessary.",
            ],
        )

    return (
        "Application-level execution failure",
        [
            "Inspect error message and trace steps.",
            "Add structured error logging for this failure type.",
            "Review the agent workflow around the failed step.",
        ],
    )


def severity_from_failure_count(count: int) -> str:
    if count >= 20:
        return "critical"
    if count >= 10:
        return "high"
    if count >= 3:
        return "medium"
    return "low"


def extract_tool_failure_evidence(executions: list[dict[str, Any]]) -> list[RootCauseEvidence]:
    evidence: list[RootCauseEvidence] = []

    for execution in executions[:5]:
        for tool_call in execution.get("tool_calls", []):
            if tool_call.get("status") != "success":
                evidence.append(
                    RootCauseEvidence(
                        source="tool_call",
                        description=f"Tool `{tool_call.get('name', 'unknown')}` failed.",
                        value=tool_call.get("status", "failed"),
                    )
                )

    return evidence


def build_failure_context(executions: list[dict[str, Any]]) -> str:
    compact_failures: list[dict[str, Any]] = []

    for execution in executions[:4]:
        compact_failures.append(
            {
                "status": execution.get("status"),
                "error_message": execution.get("error_message"),
                "latency_ms": execution.get("latency_ms"),
                "tool_calls": execution.get("tool_calls", [])[:2],
                "trace_steps": execution.get("trace_steps", [])[:3],
            }
        )

    return str(compact_failures)


async def run_root_cause_agent(
    *,
    user_id: str,
    agent_id: str,
) -> RootCauseAgentResponse:
    database = get_database()

    try:
        object_id = object_id_from_string(agent_id)
    except ValueError as exc:
        raise ValueError("Invalid agent id") from exc

    agent = await database[AGENT_COLLECTION].find_one(
        {
            "_id": object_id,
            "user_id": user_id,
        }
    )

    if agent is None:
        raise LookupError("Agent not found")

    failed_executions = await database[EXECUTION_COLLECTION].find(
        {
            "user_id": user_id,
            "agent_id": agent_id,
            "status": "failed",
        }
    ).sort("created_at", -1).to_list(length=100)

    analyzed_failures = len(failed_executions)

    if analyzed_failures == 0:
        return RootCauseAgentResponse(
            agent_id=agent_id,
            agent_name=agent["name"],
            probable_root_cause="No failed executions found",
            confidence=100,
            severity="low",
            evidence=[
                RootCauseEvidence(
                    source="execution_history",
                    description="No failed executions are recorded for this agent.",
                    value=0,
                )
            ],
            recommended_fixes=[
                "No root cause analysis needed yet. Continue monitoring this agent."
            ],
            analyzed_failures=0,
            generated_at=datetime.now(timezone.utc),
        )

    latest_failure = failed_executions[0]
    probable_root_cause, recommended_fixes = classify_error(
        latest_failure.get("error_message")
    )

    evidence: list[RootCauseEvidence] = [
        RootCauseEvidence(
            source="latest_error",
            description="Latest failed execution error message.",
            value=latest_failure.get("error_message") or "No error message provided",
        ),
        RootCauseEvidence(
            source="failure_count",
            description="Number of recent failed executions analyzed.",
            value=analyzed_failures,
        ),
    ]

    slow_failures = [
        execution
        for execution in failed_executions
        if execution.get("latency_ms", 0) >= 5000
    ]

    if slow_failures:
        evidence.append(
            RootCauseEvidence(
                source="latency",
                description="Some failed executions had high latency.",
                value=len(slow_failures),
            )
        )

    evidence.extend(extract_tool_failure_evidence(failed_executions))

    confidence = 60

    if latest_failure.get("error_message"):
        confidence += 20

    if slow_failures:
        confidence += 10

    if len(evidence) >= 3:
        confidence += 10

    confidence = min(confidence, 95)

    fallback = {
        "probable_root_cause": probable_root_cause,
        "confidence": confidence,
        "reasoning": "Rule-based analysis was used because LLM reasoning was unavailable.",
        "recommended_fixes": recommended_fixes,
    }

    llm_result, llm_used = await ask_ollama_json(
        system_prompt=(
            "You are a senior AI operations root-cause analysis agent. "
            "Analyze failed agent executions, trace steps, tool calls, latency, and errors. "
            "Return JSON with keys: probable_root_cause, confidence, reasoning, recommended_fixes."
        ),
        user_prompt=(
            f"Agent name: {agent['name']}\n"
            f"Recent failure count: {analyzed_failures}\n"
            f"Failure context: {build_failure_context(failed_executions)}"
        ),
        fallback=fallback,
    )

    probable_root_cause = str(
        llm_result.get("probable_root_cause", probable_root_cause)
    )
    confidence = float(llm_result.get("confidence", confidence))
    if confidence <= 1:
        confidence *= 100
    confidence = min(max(confidence, 0), 100)
    recommended_fixes = llm_result.get("recommended_fixes", recommended_fixes)

    if not isinstance(recommended_fixes, list):
        recommended_fixes = [str(recommended_fixes)]

    return RootCauseAgentResponse(
        agent_id=agent_id,
        agent_name=agent["name"],
        probable_root_cause=probable_root_cause,
        confidence=confidence,
        severity=severity_from_failure_count(analyzed_failures),
        evidence=evidence,
        recommended_fixes=recommended_fixes,
        analyzed_failures=analyzed_failures,
        llm_reasoning=llm_result.get("reasoning"),
        llm_used=llm_used,
        generated_at=datetime.now(timezone.utc),
    )
