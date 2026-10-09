from datetime import datetime, timezone
from typing import Any

from app.db.mongodb import get_database
from app.models.agent import object_id_from_string
from app.schemas.diagnostic_schema import (
    WorkflowEvolutionAgentResponse,
    WorkflowRecommendation,
)
from app.services.llm_service import ask_ollama_json


AGENT_COLLECTION = "agents"
EXECUTION_COLLECTION = "executions"


def severity_from_score(score: float) -> str:
    if score < 40:
        return "critical"
    if score < 60:
        return "high"
    if score < 75:
        return "medium"
    return "low"


def compact_workflow_context(executions: list[dict[str, Any]]) -> str:
    compact: list[dict[str, Any]] = []

    for execution in executions[:8]:
        compact.append(
            {
                "status": execution.get("status"),
                "latency_ms": execution.get("latency_ms"),
                "cost": execution.get("cost"),
                "tool_calls": execution.get("tool_calls", [])[:5],
                "trace_steps": execution.get("trace_steps", [])[:6],
            }
        )

    return str(compact)


def analyze_workflow_patterns(
    executions: list[dict[str, Any]],
) -> tuple[float, list[WorkflowRecommendation]]:
    recommendations: list[WorkflowRecommendation] = []

    repeated_tool_calls = 0
    slow_tool_steps = 0
    llm_step_heavy_runs = 0
    missing_retrieval_runs = 0

    for execution in executions:
        tool_names = [tool.get("name") for tool in execution.get("tool_calls", [])]
        repeated_tool_calls += len(tool_names) - len(set(tool_names))

        for tool in execution.get("tool_calls", []):
            if tool.get("duration_ms", 0) >= 3000:
                slow_tool_steps += 1

        trace_steps = execution.get("trace_steps", [])
        llm_steps = [
            step for step in trace_steps if step.get("step_type") == "llm"
        ]
        retrieval_steps = [
            step
            for step in trace_steps
            if "retriev" in str(step.get("name", "")).lower()
            or "retriev" in str(step.get("content", "")).lower()
        ]

        if len(llm_steps) >= 4:
            llm_step_heavy_runs += 1

        if not retrieval_steps and execution.get("total_tokens", 0) >= 1000:
            missing_retrieval_runs += 1

    score = 100

    if repeated_tool_calls > 0:
        score -= min(25, repeated_tool_calls * 5)
        recommendations.append(
            WorkflowRecommendation(
                title="Repeated tool calls detected",
                impact="medium",
                current_pattern="Agent repeatedly calls the same tool in a single execution.",
                suggested_pattern="Add planning memory or cache tool results inside the workflow.",
                reason="Repeated tool calls increase latency and cost.",
            )
        )

    if slow_tool_steps > 0:
        score -= min(25, slow_tool_steps * 5)
        recommendations.append(
            WorkflowRecommendation(
                title="Slow tool steps detected",
                impact="high",
                current_pattern="Workflow waits on slow tools during execution.",
                suggested_pattern="Add timeout handling, retries, caching, or async tool execution.",
                reason="Slow tools directly increase user-facing latency.",
            )
        )

    if llm_step_heavy_runs > 0:
        score -= min(20, llm_step_heavy_runs * 4)
        recommendations.append(
            WorkflowRecommendation(
                title="Too many LLM reasoning steps",
                impact="medium",
                current_pattern="Workflow uses many LLM steps before producing an answer.",
                suggested_pattern="Merge planning and synthesis steps where possible.",
                reason="Too many LLM calls increase cost and execution time.",
            )
        )

    if missing_retrieval_runs > 0:
        score -= min(20, missing_retrieval_runs * 4)
        recommendations.append(
            WorkflowRecommendation(
                title="Missing retrieval before long generation",
                impact="medium",
                current_pattern="Agent generates long answers without a retrieval step.",
                suggested_pattern="Use retriever → grounded context → final LLM response.",
                reason="Retrieval grounding can reduce hallucination risk and improve answer quality.",
            )
        )

    score = min(max(score, 0), 100)

    if not recommendations:
        recommendations.append(
            WorkflowRecommendation(
                title="Workflow pattern looks stable",
                impact="low",
                current_pattern="Trace steps and tool calls do not show major inefficiencies.",
                suggested_pattern="Continue collecting workflow traces for deeper optimization.",
                reason="No major repeated, slow, or overly complex workflow patterns detected.",
            )
        )

    return score, recommendations


async def run_workflow_evolution_agent(
    *,
    user_id: str,
    agent_id: str,
) -> WorkflowEvolutionAgentResponse:
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
    ).sort("created_at", -1).to_list(length=100)

    score, recommendations = analyze_workflow_patterns(executions)

    fallback = {
        "workflow_score": score,
        "reasoning": "Workflow evolution used deterministic trace and tool-call analysis.",
        "recommendations": [
            recommendation.model_dump() for recommendation in recommendations
        ],
    }

    llm_result, llm_used = await ask_ollama_json(
        system_prompt=(
            "You are a workflow evolution agent for AI systems. "
            "Analyze trace steps, tool calls, latency, cost, and execution status. "
            "Recommend better workflow designs. "
            "Return JSON with keys: workflow_score, reasoning, recommendations. "
            "Each recommendation must include title, impact, current_pattern, suggested_pattern, reason."
        ),
        user_prompt=(
            f"Agent name: {agent['name']}\n"
            f"Rule recommendations: {[recommendation.model_dump() for recommendation in recommendations]}\n"
            f"Workflow context: {compact_workflow_context(executions)}"
        ),
        fallback=fallback,
    )

    llm_score = llm_result.get("workflow_score", score)

    try:
        score = float(llm_score)
        if score <= 1:
            score *= 100
    except (TypeError, ValueError):
        pass

    score = min(max(score, 0), 100)

    llm_recommendations = llm_result.get("recommendations", [])
    parsed_recommendations: list[WorkflowRecommendation] = []

    if isinstance(llm_recommendations, list):
        for item in llm_recommendations:
            if isinstance(item, dict):
                try:
                    parsed_recommendations.append(
                        WorkflowRecommendation(
                            title=str(item.get("title", "Workflow recommendation")),
                            impact=item.get("impact", "medium"),
                            current_pattern=str(item.get("current_pattern", "")),
                            suggested_pattern=str(item.get("suggested_pattern", "")),
                            reason=str(item.get("reason", "")),
                        )
                    )
                except Exception:
                    continue

    if parsed_recommendations:
        recommendations = parsed_recommendations

    return WorkflowEvolutionAgentResponse(
        agent_id=agent_id,
        agent_name=agent["name"],
        workflow_score=round(score, 2),
        severity=severity_from_score(score),
        recommendations=recommendations[:20],
        llm_reasoning=llm_result.get("reasoning"),
        llm_used=llm_used,
        generated_at=datetime.now(timezone.utc),
    )