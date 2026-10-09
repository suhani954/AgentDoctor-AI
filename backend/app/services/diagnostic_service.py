import logging

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.agents.prompt_injection_agent import run_prompt_injection_agent
from app.agents.hallucination_agent import run_hallucination_agent
from app.agents.evaluation_agent import run_evaluation_agent
from app.agents.monitoring_agent import run_monitoring_agent
from app.agents.root_cause_agent import run_root_cause_agent
from app.agents.incident_commander_agent import run_incident_commander_agent
from app.agents.optimization_agent import run_optimization_agent
from app.agents.graph import run_multi_agent_diagnostic
from app.services.alert_service import create_alerts_from_diagnostic
from app.agents.workflow_evolution_agent import run_workflow_evolution_agent
from app.db.mongodb import get_database

from app.schemas.diagnostic_schema import (
    AutoDiagnosticRunResponse,
    DiagnosticReportRecord,
    IncidentReportResponse,
    PromptInjectionAgentResponse,
    HallucinationAgentResponse,
    EvaluationAgentResponse,
    WorkflowEvolutionAgentResponse,
    MonitoringAgentResponse,
    OptimizationAgentResponse,
    RootCauseAgentResponse,
    MultiAgentDiagnosticResponse,
)
from app.services.diagnostic_report_service import (
    clear_diagnostic_reports,
    list_diagnostic_reports,
    save_diagnostic_report,
)
from app.services.llm_service import ask_ollama_json


MAX_BULK_LLM_REPORTS = 100
logger = logging.getLogger(__name__)


def as_payload(response: BaseModel) -> dict:
    return response.model_dump(mode="json")


def calculate_autonomous_priority(report: MultiAgentDiagnosticResponse) -> str:
    monitoring = report.monitoring
    severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    score = 0

    if monitoring.failure_rate >= 25:
        score += 3
    elif monitoring.failure_rate > 0:
        score += 2

    if monitoring.average_latency_ms >= 5000:
        score += 2
    elif monitoring.average_latency_ms >= 2500:
        score += 1

    if monitoring.total_cost >= 1:
        score += 2
    elif monitoring.total_cost >= 0.25:
        score += 1

    for nested_report in [
        report.prompt_injection,
        report.hallucination,
        report.workflow_evolution,
        report.root_cause,
        report.incident,
    ]:
        severity = getattr(nested_report, "severity", "low") if nested_report else "low"
        score = max(score, severity_order.get(severity, 0))

    if score >= 5:
        return "critical"
    if score >= 3:
        return "high"
    if score >= 1:
        return "medium"
    return "low"


def should_use_bulk_llm(report: MultiAgentDiagnosticResponse) -> bool:
    return True


def build_bulk_llm_context(report: MultiAgentDiagnosticResponse) -> dict:
    return {
        "agent_name": report.agent_name,
        "monitoring": {
            "total_executions": report.monitoring.total_executions,
            "failure_rate": report.monitoring.failure_rate,
            "average_latency_ms": report.monitoring.average_latency_ms,
            "total_cost": report.monitoring.total_cost,
            "insights": [
                insight.model_dump(mode="json")
                for insight in report.monitoring.insights[:3]
            ],
        },
        "prompt_injection": report.prompt_injection.model_dump(mode="json")
        if report.prompt_injection
        else None,
        "hallucination": report.hallucination.model_dump(mode="json")
        if report.hallucination
        else None,
        "root_cause": report.root_cause.model_dump(mode="json")
        if report.root_cause
        else None,
        "optimization": report.optimization.model_dump(mode="json")
        if report.optimization
        else None,
        "incident": report.incident.model_dump(mode="json") if report.incident else None,
        "current_summary": report.final_summary,
    }


async def enrich_bulk_report_with_llm(
    report: MultiAgentDiagnosticResponse,
) -> MultiAgentDiagnosticResponse:
    priority = calculate_autonomous_priority(report)
    report.autonomous_priority = priority

    fallback = {
        "reasoning": "LLM triage was attempted but did not complete. The saved report includes the available diagnostic context.",
        "final_summary": report.final_summary,
        "priority": priority,
        "next_actions": [],
    }

    llm_result, llm_used = await ask_ollama_json(
        system_prompt=(
            "You are an autonomous AI operations triage agent. "
            "You receive compact diagnostics from multiple specialist agents. "
            "Decide the operational priority and write a concise executive summary. "
            "Return JSON with keys: reasoning, final_summary, priority, next_actions. "
            "Priority must be low, medium, high, or critical."
        ),
        user_prompt=str(build_bulk_llm_context(report)),
        fallback=fallback,
    )

    priority_value = str(llm_result.get("priority", priority)).lower()
    if priority_value not in {"low", "medium", "high", "critical"}:
        priority_value = priority

    report.autonomous_priority = priority_value
    report.llm_used = llm_used
    report.llm_reasoning = str(llm_result.get("reasoning", fallback["reasoning"]))

    final_summary = llm_result.get("final_summary")
    if final_summary:
        report.final_summary = str(final_summary)

    next_actions = llm_result.get("next_actions", [])
    if isinstance(next_actions, list) and next_actions:
        actions_text = " Next actions: " + "; ".join(str(action) for action in next_actions[:3])
        report.final_summary = f"{report.final_summary}{actions_text}"

    if llm_used and "LLM Triage Reasoner" not in report.executed_agents:
        report.executed_agents.append("LLM Triage Reasoner")

    return report


AGENT_COLLECTION = "agents"

async def run_monitoring_diagnostic(
    *,
    user_id: str,
    agent_id: str,
) -> MonitoringAgentResponse:
    try:
        return await run_monitoring_agent(user_id=user_id, agent_id=agent_id)
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
    

async def run_root_cause_diagnostic(
    *,
    user_id: str,
    agent_id: str,
) -> RootCauseAgentResponse:
    try:
        return await run_root_cause_agent(user_id=user_id, agent_id=agent_id)
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
    
async def run_optimization_diagnostic(*, user_id: str, agent_id: str) -> OptimizationAgentResponse:
    try:
        return await run_optimization_agent(user_id=user_id, agent_id=agent_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid agent id") from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found") from exc


async def run_incident_diagnostic(*, user_id: str, agent_id: str) -> IncidentReportResponse:
    try:
        return await run_incident_commander_agent(user_id=user_id, agent_id=agent_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid agent id") from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found") from exc
    

async def run_full_diagnostic(
    *,
    user_id: str,
    agent_id: str,
) -> MultiAgentDiagnosticResponse:
    try:
        result = await run_multi_agent_diagnostic(user_id=user_id, agent_id=agent_id)
        result.autonomous_priority = calculate_autonomous_priority(result)
        result = await enrich_bulk_report_with_llm(result)
        await save_diagnostic_report(
            user_id=user_id,
            agent_id=agent_id,
            agent_name=result.agent_name,
            report_type="full_diagnostic",
            payload=as_payload(result),
        )
        return result
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


async def get_diagnostic_reports(user_id: str) -> list[DiagnosticReportRecord]:
    return await list_diagnostic_reports(user_id)


async def clear_diagnostic_report_history(user_id: str) -> int:
    return await clear_diagnostic_reports(user_id)


async def run_auto_diagnostics(user_id: str) -> AutoDiagnosticRunResponse:
    database = get_database()
    agents = await database[AGENT_COLLECTION].find(
        {"user_id": user_id}
    ).to_list(length=100)

    reports: list[MultiAgentDiagnosticResponse] = []
    llm_enriched_count = 0

    for agent in agents:
        agent_id = str(agent["_id"])
        try:
            result = await run_multi_agent_diagnostic(
                user_id=user_id,
                agent_id=agent_id,
            )

            result.autonomous_priority = calculate_autonomous_priority(result)
            if (
                llm_enriched_count < MAX_BULK_LLM_REPORTS
                and should_use_bulk_llm(result)
            ):
                result = await enrich_bulk_report_with_llm(result)
                if result.llm_used:
                    llm_enriched_count += 1

            await save_diagnostic_report(
                user_id=user_id,
                agent_id=agent_id,
                agent_name=result.agent_name,
                report_type="auto_diagnostic",
                payload=as_payload(result),
            )

            await create_alerts_from_diagnostic(
                user_id=user_id,
                diagnostic=result,
            )
            reports.append(result)
        except Exception:
            logger.exception(
                "Auto diagnostic failed for agent_id=%s user_id=%s",
                agent_id,
                user_id,
            )
            continue

    return AutoDiagnosticRunResponse(
        agents_scanned=len(agents),
        reports_created=len(reports),
        reports=reports,
    )


async def run_prompt_injection_diagnostic(
    *,
    user_id: str,
    agent_id: str,
) -> PromptInjectionAgentResponse:
    try:
        return await run_prompt_injection_agent(user_id=user_id, agent_id=agent_id)
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
    

async def run_hallucination_diagnostic(
    *,
    user_id: str,
    agent_id: str,
) -> HallucinationAgentResponse:
    try:
        return await run_hallucination_agent(user_id=user_id, agent_id=agent_id)
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
    

async def run_evaluation_diagnostic(
    *,
    user_id: str,
    agent_id: str,
) -> EvaluationAgentResponse:
    try:
        return await run_evaluation_agent(user_id=user_id, agent_id=agent_id)
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
    
async def run_workflow_evolution_diagnostic(
    *,
    user_id: str,
    agent_id: str,
) -> WorkflowEvolutionAgentResponse:
    try:
        return await run_workflow_evolution_agent(user_id=user_id, agent_id=agent_id)
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
