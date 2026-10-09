from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.schemas.auth_schema import UserResponse

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

from app.services.diagnostic_service import (
    run_incident_diagnostic,
    run_prompt_injection_diagnostic,
    run_hallucination_diagnostic,
    run_evaluation_diagnostic,
    run_monitoring_diagnostic,
    run_optimization_diagnostic,
    run_workflow_evolution_diagnostic,
    run_root_cause_diagnostic,
    run_full_diagnostic,
    get_diagnostic_reports,
    clear_diagnostic_report_history,
    run_auto_diagnostics,
)

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


@router.get("/reports", response_model=list[DiagnosticReportRecord])
async def list_diagnostic_reports_route(
    current_user: UserResponse = Depends(get_current_user),
) -> list[DiagnosticReportRecord]:
    return await get_diagnostic_reports(current_user.id)


@router.delete("/reports")
async def clear_diagnostic_reports_route(
    current_user: UserResponse = Depends(get_current_user),
) -> dict[str, int]:
    deleted_count = await clear_diagnostic_report_history(current_user.id)
    return {"deleted_count": deleted_count}


@router.post("/auto-run", response_model=AutoDiagnosticRunResponse)
async def run_auto_diagnostics_route(
    current_user: UserResponse = Depends(get_current_user),
) -> AutoDiagnosticRunResponse:
    return await run_auto_diagnostics(current_user.id)


@router.post("/monitor/{agent_id}", response_model=MonitoringAgentResponse)
async def run_monitoring_diagnostic_route(
    agent_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> MonitoringAgentResponse:
    return await run_monitoring_diagnostic(
        user_id=current_user.id,
        agent_id=agent_id,
    )


@router.post("/root-cause/{agent_id}", response_model=RootCauseAgentResponse)
async def run_root_cause_diagnostic_route(
    agent_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> RootCauseAgentResponse:
    return await run_root_cause_diagnostic(
        user_id=current_user.id,
        agent_id=agent_id,
    )

@router.post("/optimize/{agent_id}", response_model=OptimizationAgentResponse)
async def run_optimization_diagnostic_route(
    agent_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> OptimizationAgentResponse:
    return await run_optimization_diagnostic(user_id=current_user.id, agent_id=agent_id)


@router.post("/incident/{agent_id}", response_model=IncidentReportResponse)
async def run_incident_diagnostic_route(
    agent_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> IncidentReportResponse:
    return await run_incident_diagnostic(user_id=current_user.id, agent_id=agent_id)


@router.post("/run/{agent_id}", response_model=MultiAgentDiagnosticResponse)
async def run_full_diagnostic_route(
    agent_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> MultiAgentDiagnosticResponse:
    return await run_full_diagnostic(
        user_id=current_user.id,
        agent_id=agent_id,
    )

@router.post(
    "/prompt-injection/{agent_id}",
    response_model=PromptInjectionAgentResponse,
)
async def run_prompt_injection_diagnostic_route(
    agent_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> PromptInjectionAgentResponse:
    return await run_prompt_injection_diagnostic(
        user_id=current_user.id,
        agent_id=agent_id,
    )


@router.post(
    "/hallucination/{agent_id}",
    response_model=HallucinationAgentResponse,
)
async def run_hallucination_diagnostic_route(
    agent_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> HallucinationAgentResponse:
    return await run_hallucination_diagnostic(
        user_id=current_user.id,
        agent_id=agent_id,
    )


@router.post(
    "/evaluate/{agent_id}",
    response_model=EvaluationAgentResponse,
)
async def run_evaluation_diagnostic_route(
    agent_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> EvaluationAgentResponse:
    return await run_evaluation_diagnostic(
        user_id=current_user.id,
        agent_id=agent_id,
    )


@router.post(
    "/workflow-evolution/{agent_id}",
    response_model=WorkflowEvolutionAgentResponse,
)
async def run_workflow_evolution_diagnostic_route(
    agent_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> WorkflowEvolutionAgentResponse:
    return await run_workflow_evolution_diagnostic(
        user_id=current_user.id,
        agent_id=agent_id,
    )
