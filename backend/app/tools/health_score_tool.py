from app.db.mongodb import get_database
from app.models.agent import object_id_from_string
from app.schemas.analytics_schema import HealthScoreResponse


AGENT_COLLECTION = "agents"
EXECUTION_COLLECTION = "executions"


def percentage(part: int | float, total: int | float) -> float:
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def clamp_score(value: float) -> float:
    return max(0, min(100, round(value, 2)))


def get_grade(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Fair"
    if score >= 40:
        return "Poor"
    return "Critical"


def build_reasons(
    *,
    failure_rate: float,
    average_latency_ms: float,
    average_cost: float,
    total_executions: int,
) -> list[str]:
    reasons: list[str] = []

    if total_executions == 0:
        return ["No executions recorded yet. Health score is based on lack of data."]

    if failure_rate == 0:
        reasons.append("No failures recorded for this agent.")
    elif failure_rate <= 10:
        reasons.append("Failure rate is low.")
    elif failure_rate <= 30:
        reasons.append("Failure rate needs attention.")
    else:
        reasons.append("Failure rate is high and should be investigated.")

    if average_latency_ms <= 2000:
        reasons.append("Average latency is healthy.")
    elif average_latency_ms <= 5000:
        reasons.append("Average latency is moderate.")
    else:
        reasons.append("Average latency is high.")

    if average_cost <= 0.01:
        reasons.append("Average execution cost is efficient.")
    elif average_cost <= 0.05:
        reasons.append("Average execution cost is acceptable.")
    else:
        reasons.append("Average execution cost is high.")

    return reasons


async def calculate_agent_health_score(
    *,
    user_id: str,
    agent_id: str,
) -> HealthScoreResponse:
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
    ).to_list(length=1000)

    total_executions = len(executions)

    if total_executions == 0:
        return HealthScoreResponse(
            agent_id=agent_id,
            agent_name=agent["name"],
            score=50,
            grade="Insufficient Data",
            reliability_score=50,
            latency_score=50,
            cost_efficiency_score=50,
            failure_rate=0,
            average_latency_ms=0,
            average_cost=0,
            total_executions=0,
            reasons=["No executions recorded yet. Add execution logs to calculate a stronger health score."],
        )

    failed_executions = len(
        [execution for execution in executions if execution.get("status") == "failed"]
    )

    failure_rate = percentage(failed_executions, total_executions)

    average_latency_ms = round(
        sum(execution.get("latency_ms", 0) for execution in executions)
        / total_executions,
        2,
    )

    average_cost = round(
        sum(execution.get("cost", 0) for execution in executions)
        / total_executions,
        6,
    )

    reliability_score = clamp_score(100 - failure_rate)

    if average_latency_ms <= 2000:
        latency_score = 100
    elif average_latency_ms <= 5000:
        latency_score = 75
    elif average_latency_ms <= 10000:
        latency_score = 45
    else:
        latency_score = 20

    if average_cost <= 0.01:
        cost_efficiency_score = 100
    elif average_cost <= 0.05:
        cost_efficiency_score = 75
    elif average_cost <= 0.15:
        cost_efficiency_score = 45
    else:
        cost_efficiency_score = 20

    final_score = round(
        reliability_score * 0.45
        + latency_score * 0.30
        + cost_efficiency_score * 0.25
    )

    reasons = build_reasons(
        failure_rate=failure_rate,
        average_latency_ms=average_latency_ms,
        average_cost=average_cost,
        total_executions=total_executions,
    )

    return HealthScoreResponse(
        agent_id=agent_id,
        agent_name=agent["name"],
        score=final_score,
        grade=get_grade(final_score),
        reliability_score=reliability_score,
        latency_score=latency_score,
        cost_efficiency_score=cost_efficiency_score,
        failure_rate=failure_rate,
        average_latency_ms=average_latency_ms,
        average_cost=average_cost,
        total_executions=total_executions,
        reasons=reasons,
    )