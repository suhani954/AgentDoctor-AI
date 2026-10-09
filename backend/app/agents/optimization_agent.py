from datetime import datetime, timezone

from app.db.mongodb import get_database
from app.models.agent import object_id_from_string
from app.schemas.diagnostic_schema import (
    OptimizationAgentResponse,
    OptimizationRecommendation,
)
from app.services.llm_service import ask_ollama_json

AGENT_COLLECTION = "agents"
EXECUTION_COLLECTION = "executions"


async def run_optimization_agent(*, user_id: str, agent_id: str) -> OptimizationAgentResponse:
    database = get_database()

    try:
        object_id = object_id_from_string(agent_id)
    except ValueError as exc:
        raise ValueError("Invalid agent id") from exc

    agent = await database[AGENT_COLLECTION].find_one({"_id": object_id, "user_id": user_id})
    if agent is None:
        raise LookupError("Agent not found")

    executions = await database[EXECUTION_COLLECTION].find(
        {"user_id": user_id, "agent_id": agent_id}
    ).sort("created_at", -1).to_list(length=500)

    if not executions:
        return OptimizationAgentResponse(
            agent_id=agent_id,
            agent_name=agent["name"],
            total_cost=0,
            average_cost=0,
            average_latency_ms=0,
            total_tokens=0,
            recommendations=[
                OptimizationRecommendation(
                    title="No execution data",
                    impact="low",
                    description="Add execution logs before running optimization analysis.",
                )
            ],
            generated_at=datetime.now(timezone.utc),
        )

    total_cost = round(sum(item.get("cost", 0) for item in executions), 6)
    total_tokens = sum(item.get("total_tokens", 0) for item in executions)
    average_cost = round(total_cost / len(executions), 6)
    average_latency_ms = round(
        sum(item.get("latency_ms", 0) for item in executions) / len(executions),
        2,
    )

    recommendations: list[OptimizationRecommendation] = []

    if average_cost > 0.05:
        recommendations.append(
            OptimizationRecommendation(
                title="High average execution cost",
                impact="high",
                description="Average execution cost is high. Consider using a smaller model for simple tasks.",
                expected_savings_percent=35,
            )
        )

    if average_latency_ms > 5000:
        recommendations.append(
            OptimizationRecommendation(
                title="High latency detected",
                impact="high",
                description="Average latency is high. Review slow tools and long reasoning chains.",
                expected_savings_percent=None,
            )
        )

    repeated_tool_calls = 0
    for execution in executions:
        names = [tool.get("name") for tool in execution.get("tool_calls", [])]
        repeated_tool_calls += len(names) - len(set(names))

    if repeated_tool_calls > 0:
        recommendations.append(
            OptimizationRecommendation(
                title="Repeated tool calls detected",
                impact="medium",
                description="Some executions call the same tool multiple times. Add caching or better planning.",
                expected_savings_percent=20,
            )
        )

    if total_tokens > 100000:
        recommendations.append(
            OptimizationRecommendation(
                title="High token usage",
                impact="medium",
                description="Token usage is high. Add prompt compression or summarize long context.",
                expected_savings_percent=25,
            )
        )

    if not recommendations:
        recommendations.append(
            OptimizationRecommendation(
                title="No major optimization issue",
                impact="low",
                description="Cost, latency, and token usage look acceptable for current execution data.",
            )
        )

    fallback = {
        "reasoning": "Rule-based optimization analysis was used because LLM reasoning was unavailable.",
        "recommendations": [item.model_dump() for item in recommendations],
    }

    llm_result, llm_used = await ask_ollama_json(
        system_prompt=(
            "You are a senior AI cost and performance optimization agent. "
            "Analyze agent executions and recommend concrete improvements. "
            "Return JSON with keys: reasoning and recommendations. "
            "Each recommendation must have title, impact, description, expected_savings_percent."
        ),
        user_prompt=(
            f"Agent name: {agent['name']}\n"
            f"Execution count: {len(executions)}\n"
            f"Total cost: {total_cost}\n"
            f"Average cost: {average_cost}\n"
            f"Average latency ms: {average_latency_ms}\n"
            f"Total tokens: {total_tokens}\n"
            f"Sample executions: {executions[:5]}"
        ),
        fallback=fallback,
    )

    llm_recommendations = llm_result.get("recommendations")
    if isinstance(llm_recommendations, list):
        parsed_recommendations: list[OptimizationRecommendation] = []
        for item in llm_recommendations:
            if isinstance(item, dict):
                try:
                    parsed_recommendations.append(
                        OptimizationRecommendation(
                            title=str(item.get("title", "Optimization recommendation")),
                            impact=item.get("impact", "medium"),
                            description=str(item.get("description", "")),
                            expected_savings_percent=item.get("expected_savings_percent"),
                        )
                    )
                except Exception:
                    continue
        if parsed_recommendations:
            recommendations = parsed_recommendations

    return OptimizationAgentResponse(
        agent_id=agent_id,
        agent_name=agent["name"],
        total_cost=total_cost,
        average_cost=average_cost,
        average_latency_ms=average_latency_ms,
        total_tokens=total_tokens,
        recommendations=recommendations,
        llm_reasoning=llm_result.get("reasoning"),
        llm_used=llm_used,
        generated_at=datetime.now(timezone.utc),
    )
