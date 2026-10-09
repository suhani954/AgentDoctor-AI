from app.db.mongodb import get_database
from app.models.alert import alert_document, serialize_alert
from app.schemas.diagnostic_schema import AlertResponse


ALERT_COLLECTION = "alerts"


async def create_alert(
    *,
    user_id: str,
    agent_id: str,
    agent_name: str,
    title: str,
    severity: str,
    message: str,
    source: str,
) -> AlertResponse:
    database = get_database()

    document = alert_document(
        user_id=user_id,
        agent_id=agent_id,
        agent_name=agent_name,
        title=title,
        severity=severity,
        message=message,
        source=source,
    )

    result = await database[ALERT_COLLECTION].insert_one(document)
    created_alert = await database[ALERT_COLLECTION].find_one({"_id": result.inserted_id})

    return AlertResponse(**serialize_alert(created_alert))


async def list_alerts(user_id: str) -> list[AlertResponse]:
    database = get_database()

    cursor = (
        database[ALERT_COLLECTION]
        .find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(100)
    )

    alerts = await cursor.to_list(length=100)

    return [AlertResponse(**serialize_alert(alert)) for alert in alerts]


async def create_alerts_from_diagnostic(
    *,
    user_id: str,
    diagnostic,
) -> list[AlertResponse]:
    alerts: list[AlertResponse] = []

    monitoring = diagnostic.monitoring

    if monitoring.failure_rate >= 30:
        alerts.append(
            await create_alert(
                user_id=user_id,
                agent_id=diagnostic.agent_id,
                agent_name=diagnostic.agent_name,
                title="High failure rate detected",
                severity="high",
                message=f"{diagnostic.agent_name} has failure rate of {monitoring.failure_rate}%.",
                source="monitoring_agent",
            )
        )

    if monitoring.average_latency_ms >= 5000:
        alerts.append(
            await create_alert(
                user_id=user_id,
                agent_id=diagnostic.agent_id,
                agent_name=diagnostic.agent_name,
                title="High latency detected",
                severity="medium",
                message=f"{diagnostic.agent_name} average latency is {monitoring.average_latency_ms} ms.",
                source="monitoring_agent",
            )
        )

    if monitoring.total_cost >= 1:
        alerts.append(
            await create_alert(
                user_id=user_id,
                agent_id=diagnostic.agent_id,
                agent_name=diagnostic.agent_name,
                title="Cost spike detected",
                severity="medium",
                message=f"{diagnostic.agent_name} total tracked cost is {monitoring.total_cost}.",
                source="optimization_agent",
            )
        )

    if diagnostic.prompt_injection and diagnostic.prompt_injection.risk_score >= 60:
        alerts.append(
            await create_alert(
                user_id=user_id,
                agent_id=diagnostic.agent_id,
                agent_name=diagnostic.agent_name,
                title="Prompt injection risk detected",
                severity=diagnostic.prompt_injection.severity,
                message=f"Prompt injection risk score is {diagnostic.prompt_injection.risk_score}.",
                source="prompt_injection_agent",
            )
        )

    if diagnostic.hallucination and diagnostic.hallucination.hallucination_risk >= 60:
        alerts.append(
            await create_alert(
                user_id=user_id,
                agent_id=diagnostic.agent_id,
                agent_name=diagnostic.agent_name,
                title="Hallucination risk detected",
                severity=diagnostic.hallucination.severity,
                message=f"Hallucination risk score is {diagnostic.hallucination.hallucination_risk}.",
                source="hallucination_agent",
            )
        )

    return alerts