import logging

from app.db.mongodb import get_database
from app.schemas.diagnostic_schema import SchedulerRunResponse
from app.services.alert_service import create_alerts_from_diagnostic
from app.services.diagnostic_report_service import save_diagnostic_report
from app.services.diagnostic_service import (
    MAX_BULK_LLM_REPORTS,
    as_payload,
    calculate_autonomous_priority,
    enrich_bulk_report_with_llm,
    should_use_bulk_llm,
)
from app.agents.graph import run_multi_agent_diagnostic


AGENT_COLLECTION = "agents"
logger = logging.getLogger(__name__)


async def run_scheduled_diagnostics_for_user(user_id: str) -> SchedulerRunResponse:
    database = get_database()

    agents = await database[AGENT_COLLECTION].find(
        {"user_id": user_id}
    ).to_list(length=100)

    reports_created = 0
    alerts_created = 0
    llm_enriched_count = 0

    for agent in agents:
        agent_id = str(agent["_id"])

        try:
            diagnostic = await run_multi_agent_diagnostic(
                user_id=user_id,
                agent_id=agent_id,
            )

            diagnostic.autonomous_priority = calculate_autonomous_priority(diagnostic)
            if (
                llm_enriched_count < MAX_BULK_LLM_REPORTS
                and should_use_bulk_llm(diagnostic)
            ):
                diagnostic = await enrich_bulk_report_with_llm(diagnostic)
                if diagnostic.llm_used:
                    llm_enriched_count += 1

            await save_diagnostic_report(
                user_id=user_id,
                agent_id=agent_id,
                agent_name=diagnostic.agent_name,
                report_type="scheduled_diagnostic",
                payload=as_payload(diagnostic),
            )

            reports_created += 1

            alerts = await create_alerts_from_diagnostic(
                user_id=user_id,
                diagnostic=diagnostic,
            )

            alerts_created += len(alerts)
        except Exception:
            logger.exception(
                "Scheduled diagnostic failed for agent_id=%s user_id=%s",
                agent_id,
                user_id,
            )
            continue

    return SchedulerRunResponse(
        agents_scanned=len(agents),
        reports_created=reports_created,
        alerts_created=alerts_created,
    )
