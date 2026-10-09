from fastapi import HTTPException, status
from app.tools.health_score_tool import calculate_agent_health_score

from app.db.mongodb import get_database
from app.schemas.analytics_schema import (
    CostAnalyticsResponse,
    CostByAgent,
    FailureAnalyticsResponse,
    FailureByAgent,
    LatencyAnalyticsResponse,
    LatencyByAgent,
    OverviewAnalyticsResponse,
    HealthScoreResponse
)


AGENT_COLLECTION = "agents"
EXECUTION_COLLECTION = "executions"


def percentage(part: int | float, total: int | float) -> float:
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


async def get_agent_name_map(user_id: str) -> dict[str, str]:
    database = get_database()

    cursor = database[AGENT_COLLECTION].find({"user_id": user_id})
    agents = await cursor.to_list(length=1000)

    return {str(agent["_id"]): agent["name"] for agent in agents}


async def get_overview_analytics(user_id: str) -> OverviewAnalyticsResponse:
    database = get_database()

    total_agents = await database[AGENT_COLLECTION].count_documents({"user_id": user_id})
    total_executions = await database[EXECUTION_COLLECTION].count_documents(
        {"user_id": user_id}
    )
    successful_executions = await database[EXECUTION_COLLECTION].count_documents(
        {
            "user_id": user_id,
            "status": "success",
        }
    )
    failed_executions = await database[EXECUTION_COLLECTION].count_documents(
        {
            "user_id": user_id,
            "status": "failed",
        }
    )

    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": None,
                "total_cost": {"$sum": "$cost"},
                "average_latency_ms": {"$avg": "$latency_ms"},
            }
        },
    ]

    result = await database[EXECUTION_COLLECTION].aggregate(pipeline).to_list(length=1)
    aggregate = result[0] if result else {}

    return OverviewAnalyticsResponse(
        total_agents=total_agents,
        total_executions=total_executions,
        success_rate=percentage(successful_executions, total_executions),
        failure_rate=percentage(failed_executions, total_executions),
        total_cost=round(aggregate.get("total_cost", 0), 6),
        average_latency_ms=round(aggregate.get("average_latency_ms", 0) or 0, 2),
    )


async def get_cost_analytics(user_id: str) -> CostAnalyticsResponse:
    database = get_database()
    agent_names = await get_agent_name_map(user_id)

    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": "$agent_id",
                "total_cost": {"$sum": "$cost"},
                "total_tokens": {"$sum": "$total_tokens"},
                "execution_count": {"$sum": 1},
            }
        },
        {"$sort": {"total_cost": -1}},
    ]

    rows = await database[EXECUTION_COLLECTION].aggregate(pipeline).to_list(length=100)

    cost_by_agent = [
        CostByAgent(
            agent_id=row["_id"],
            agent_name=agent_names.get(row["_id"], "Unknown Agent"),
            total_cost=round(row.get("total_cost", 0), 6),
            total_tokens=row.get("total_tokens", 0),
            execution_count=row.get("execution_count", 0),
        )
        for row in rows
    ]

    total_cost = sum(item.total_cost for item in cost_by_agent)
    total_tokens = sum(item.total_tokens for item in cost_by_agent)

    return CostAnalyticsResponse(
        total_cost=round(total_cost, 6),
        total_tokens=total_tokens,
        cost_by_agent=cost_by_agent,
    )


async def get_latency_analytics(user_id: str) -> LatencyAnalyticsResponse:
    database = get_database()
    agent_names = await get_agent_name_map(user_id)

    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": "$agent_id",
                "average_latency_ms": {"$avg": "$latency_ms"},
                "max_latency_ms": {"$max": "$latency_ms"},
                "execution_count": {"$sum": 1},
            }
        },
        {"$sort": {"average_latency_ms": -1}},
    ]

    rows = await database[EXECUTION_COLLECTION].aggregate(pipeline).to_list(length=100)

    latency_by_agent = [
        LatencyByAgent(
            agent_id=row["_id"],
            agent_name=agent_names.get(row["_id"], "Unknown Agent"),
            average_latency_ms=round(row.get("average_latency_ms", 0) or 0, 2),
            max_latency_ms=row.get("max_latency_ms", 0),
            execution_count=row.get("execution_count", 0),
        )
        for row in rows
    ]

    if latency_by_agent:
        average_latency_ms = round(
            sum(item.average_latency_ms for item in latency_by_agent)
            / len(latency_by_agent),
            2,
        )
        max_latency_ms = max(item.max_latency_ms for item in latency_by_agent)
    else:
        average_latency_ms = 0
        max_latency_ms = 0

    return LatencyAnalyticsResponse(
        average_latency_ms=average_latency_ms,
        max_latency_ms=max_latency_ms,
        latency_by_agent=latency_by_agent,
    )


async def get_failure_analytics(user_id: str) -> FailureAnalyticsResponse:
    database = get_database()
    agent_names = await get_agent_name_map(user_id)

    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": "$agent_id",
                "total_executions": {"$sum": 1},
                "failed_executions": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "failed"]}, 1, 0]
                    }
                },
            }
        },
        {"$sort": {"failed_executions": -1}},
    ]

    rows = await database[EXECUTION_COLLECTION].aggregate(pipeline).to_list(length=100)

    failures_by_agent = [
        FailureByAgent(
            agent_id=row["_id"],
            agent_name=agent_names.get(row["_id"], "Unknown Agent"),
            failed_executions=row.get("failed_executions", 0),
            total_executions=row.get("total_executions", 0),
            failure_rate=percentage(
                row.get("failed_executions", 0),
                row.get("total_executions", 0),
            ),
        )
        for row in rows
    ]

    total_failures = sum(item.failed_executions for item in failures_by_agent)
    total_executions = sum(item.total_executions for item in failures_by_agent)

    return FailureAnalyticsResponse(
        total_failures=total_failures,
        failure_rate=percentage(total_failures, total_executions),
        failures_by_agent=failures_by_agent,
    )


async def get_agent_health_score(
    user_id: str,
    agent_id: str,
) -> HealthScoreResponse:
    try:
        return await calculate_agent_health_score(user_id=user_id, agent_id=agent_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid agent id",
        ) from exc
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        ) from exc