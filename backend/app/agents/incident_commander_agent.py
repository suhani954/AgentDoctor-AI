from datetime import datetime, timezone

from app.agents.root_cause_agent import run_root_cause_agent
from app.db.mongodb import get_database
from app.models.agent import object_id_from_string
from app.schemas.diagnostic_schema import IncidentReportResponse
from app.services.llm_service import ask_ollama_json

AGENT_COLLECTION = "agents"
EXECUTION_COLLECTION = "executions"


def incident_severity(failure_count: int) -> str:
    if failure_count >= 20:
        return "critical"
    if failure_count >= 10:
        return "high"
    if failure_count >= 3:
        return "medium"
    return "low"


async def run_incident_commander_agent(*, user_id: str, agent_id: str) -> IncidentReportResponse:
    database = get_database()

    try:
        object_id = object_id_from_string(agent_id)
    except ValueError as exc:
        raise ValueError("Invalid agent id") from exc

    agent = await database[AGENT_COLLECTION].find_one({"_id": object_id, "user_id": user_id})
    if agent is None:
        raise LookupError("Agent not found")

    failed_executions = await database[EXECUTION_COLLECTION].find(
        {"user_id": user_id, "agent_id": agent_id, "status": "failed"}
    ).sort("created_at", -1).to_list(length=100)

    failure_count = len(failed_executions)

    if failure_count == 0:
        fallback = {
            "reasoning": "No failed executions were found, so no active incident is present.",
            "summary": "No active incident detected.",
            "probable_cause": "No failed executions found.",
            "recommended_actions": ["Continue monitoring this agent."],
        }
        llm_result, llm_used = await ask_ollama_json(
            system_prompt=(
                "You are an autonomous AI incident commander. "
                "The agent has no failed executions. "
                "Return JSON with keys: reasoning, summary, probable_cause, recommended_actions."
            ),
            user_prompt=str({"agent_name": agent["name"], "failure_count": 0}),
            fallback=fallback,
        )
        recommended_actions = llm_result.get(
            "recommended_actions",
            fallback["recommended_actions"],
        )
        if not isinstance(recommended_actions, list):
            recommended_actions = [str(recommended_actions)]

        return IncidentReportResponse(
            agent_id=agent_id,
            agent_name=agent["name"],
            severity="low",
            affected_executions=0,
            summary=str(llm_result.get("summary", fallback["summary"])),
            probable_cause=str(llm_result.get("probable_cause", fallback["probable_cause"])),
            recommended_actions=recommended_actions,
            llm_reasoning=llm_result.get("reasoning"),
            llm_used=llm_used,
            generated_at=datetime.now(timezone.utc),
        )

    root_cause = await run_root_cause_agent(user_id=user_id, agent_id=agent_id)
    fallback = {
        "reasoning": "LLM incident commander reasoning was unavailable.",
        "summary": f"{failure_count} failed executions were detected for {agent['name']}.",
        "probable_cause": root_cause.probable_root_cause,
        "recommended_actions": root_cause.recommended_fixes,
    }

    llm_result, llm_used = await ask_ollama_json(
        system_prompt=(
            "You are an autonomous AI incident commander. "
            "Write a concise incident summary from failures and root cause analysis. "
            "Return JSON with keys: reasoning, summary, probable_cause, recommended_actions."
        ),
        user_prompt=str(
            {
                "agent_name": agent["name"],
                "failure_count": failure_count,
                "root_cause": root_cause.model_dump(mode="json"),
                "sample_failures": [
                    {
                        "error_message": execution.get("error_message"),
                        "latency_ms": execution.get("latency_ms"),
                        "tool_calls": execution.get("tool_calls", [])[:2],
                    }
                    for execution in failed_executions[:5]
                ],
            }
        ),
        fallback=fallback,
    )

    recommended_actions = llm_result.get(
        "recommended_actions",
        root_cause.recommended_fixes,
    )
    if not isinstance(recommended_actions, list):
        recommended_actions = [str(recommended_actions)]

    return IncidentReportResponse(
        agent_id=agent_id,
        agent_name=agent["name"],
        severity=incident_severity(failure_count),
        affected_executions=failure_count,
        summary=str(llm_result.get("summary", fallback["summary"])),
        probable_cause=str(llm_result.get("probable_cause", root_cause.probable_root_cause)),
        recommended_actions=recommended_actions,
        llm_reasoning=llm_result.get("reasoning"),
        llm_used=llm_used,
        generated_at=datetime.now(timezone.utc),
    )
