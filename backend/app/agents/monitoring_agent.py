from datetime import datetime, timezone

from app.db.mongodb import get_database
from app.models.agent import object_id_from_string
from app.schemas.diagnostic_schema import MonitoringAgentResponse, MonitoringInsight
from app.services.llm_service import ask_ollama_json


AGENT_COLLECTION = "agents"
EXECUTION_COLLECTION = "executions"


def percentage(part: int | float, total: int | float) -> float:
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def severity_from_failure_rate(failure_rate: float) -> str:
    if failure_rate >= 50:
        return "critical"
    if failure_rate >= 30:
        return "high"
    if failure_rate >= 10:
        return "medium"
    return "low"


def severity_from_latency(average_latency_ms: float) -> str:
    if average_latency_ms >= 10000:
        return "critical"
    if average_latency_ms >= 5000:
        return "high"
    if average_latency_ms >= 2500:
        return "medium"
    return "low"


def severity_from_cost(total_cost: float) -> str:
    if total_cost >= 5:
        return "critical"
    if total_cost >= 1:
        return "high"
    if total_cost >= 0.25:
        return "medium"
    return "low"


async def run_monitoring_agent(
    *,
    user_id: str,
    agent_id: str,
) -> MonitoringAgentResponse:
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

    executions = await database[EXECUTION_COLLECTION].find(
        {
            "user_id": user_id,
            "agent_id": agent_id,
        }
    ).sort("created_at", -1).to_list(length=500)

    total_executions = len(executions)

    if total_executions == 0:
        fallback = {
            "reasoning": "No execution data is available yet, so the monitoring agent cannot infer runtime behavior.",
            "recommended_actions": [
                "Log executions for this agent before running deeper diagnostics."
            ],
        }
        llm_result, llm_used = await ask_ollama_json(
            system_prompt=(
                "You are an autonomous AI monitoring agent. "
                "The agent has no execution data yet. "
                "Return JSON with keys: reasoning and recommended_actions."
            ),
            user_prompt=str({"agent_name": agent["name"], "total_executions": 0}),
            fallback=fallback,
        )
        recommended_actions = llm_result.get(
            "recommended_actions",
            fallback["recommended_actions"],
        )
        if not isinstance(recommended_actions, list):
            recommended_actions = [str(recommended_actions)]

        return MonitoringAgentResponse(
            agent_id=agent_id,
            agent_name=agent["name"],
            total_executions=0,
            failure_rate=0,
            average_latency_ms=0,
            total_cost=0,
            insights=[
                MonitoringInsight(
                    title="No execution data",
                    severity="low",
                    description="This agent does not have execution logs yet.",
                    metric="executions",
                    value=0,
                )
            ],
            recommended_actions=recommended_actions,
            llm_reasoning=llm_result.get("reasoning"),
            llm_used=llm_used,
            generated_at=datetime.now(timezone.utc),
        )

    failed_executions = [
        execution for execution in executions if execution.get("status") == "failed"
    ]

    failure_rate = percentage(len(failed_executions), total_executions)

    average_latency_ms = round(
        sum(execution.get("latency_ms", 0) for execution in executions)
        / total_executions,
        2,
    )

    total_cost = round(
        sum(execution.get("cost", 0) for execution in executions),
        6,
    )

    insights: list[MonitoringInsight] = []
    recommended_actions: list[str] = []

    if failure_rate > 0:
        insights.append(
            MonitoringInsight(
                title="Failure rate detected",
                severity=severity_from_failure_rate(failure_rate),
                description=f"This agent has a failure rate of {failure_rate}%.",
                metric="failure_rate",
                value=failure_rate,
            )
        )

    if average_latency_ms > 2500:
        insights.append(
            MonitoringInsight(
                title="Latency increase detected",
                severity=severity_from_latency(average_latency_ms),
                description=f"Average latency is {average_latency_ms} ms.",
                metric="average_latency_ms",
                value=average_latency_ms,
            )
        )

    if total_cost > 0.25:
        insights.append(
            MonitoringInsight(
                title="Cost usage detected",
                severity=severity_from_cost(total_cost),
                description=f"Total recorded cost is {total_cost}.",
                metric="total_cost",
                value=total_cost,
            )
        )

    if not insights:
        insights.append(
            MonitoringInsight(
                title="Agent operating normally",
                severity="low",
                description="No major failure, latency, or cost issues detected.",
                metric="overall_health",
                value="normal",
            )
        )

    if failure_rate >= 10:
        recommended_actions.append(
            "Run root cause analysis on recent failed executions."
        )

    if average_latency_ms >= 2500:
        recommended_actions.append(
            "Inspect slow trace steps and tool calls in the flight recorder."
        )

    if total_cost >= 0.25:
        recommended_actions.append(
            "Review token usage and model selection for cost optimization."
        )

    if not recommended_actions:
        recommended_actions.append(
            "Continue monitoring this agent and collect more execution data."
        )

    fallback = {
        "reasoning": "LLM monitoring reasoning was unavailable.",
        "recommended_actions": recommended_actions,
    }

    llm_result, llm_used = await ask_ollama_json(
        system_prompt=(
            "You are an autonomous AI monitoring agent. "
            "Reason about execution health, latency, cost, and reliability. "
            "Return JSON with keys: reasoning and recommended_actions. "
            "recommended_actions must be a short list of concrete actions."
        ),
        user_prompt=str(
            {
                "agent_name": agent["name"],
                "total_executions": total_executions,
                "failure_rate": failure_rate,
                "average_latency_ms": average_latency_ms,
                "total_cost": total_cost,
                "insights": [insight.model_dump(mode="json") for insight in insights],
                "sample_executions": [
                    {
                        "status": execution.get("status"),
                        "error_message": execution.get("error_message"),
                        "latency_ms": execution.get("latency_ms"),
                        "cost": execution.get("cost"),
                    }
                    for execution in executions[:5]
                ],
            }
        ),
        fallback=fallback,
    )

    llm_actions = llm_result.get("recommended_actions")
    if isinstance(llm_actions, list) and llm_actions:
        recommended_actions = [str(action) for action in llm_actions[:5]]

    return MonitoringAgentResponse(
        agent_id=agent_id,
        agent_name=agent["name"],
        total_executions=total_executions,
        failure_rate=failure_rate,
        average_latency_ms=average_latency_ms,
        total_cost=total_cost,
        insights=insights,
        recommended_actions=recommended_actions,
        llm_reasoning=llm_result.get("reasoning"),
        llm_used=llm_used,
        generated_at=datetime.now(timezone.utc),
    )
