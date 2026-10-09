from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SeverityLevel = Literal["low", "medium", "high", "critical"]


class MonitoringInsight(BaseModel):
    title: str
    severity: SeverityLevel
    description: str
    metric: str
    value: float | int | str


class MonitoringAgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    total_executions: int
    failure_rate: float
    average_latency_ms: float
    total_cost: float
    insights: list[MonitoringInsight] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    llm_reasoning: str | None = None
    llm_used: bool = False
    generated_at: datetime


class PromptInjectionFinding(BaseModel):
    pattern: str
    evidence: str
    severity: SeverityLevel


class PromptInjectionAgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    risk_score: float
    severity: SeverityLevel
    findings: list[PromptInjectionFinding] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    llm_reasoning: str | None = None
    llm_used: bool = False
    generated_at: datetime


class HallucinationFinding(BaseModel):
    claim: str
    reason: str
    risk: SeverityLevel


class HallucinationAgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    hallucination_risk: float
    severity: SeverityLevel
    findings: list[HallucinationFinding] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    llm_reasoning: str | None = None
    llm_used: bool = False
    generated_at: datetime


class EvaluationTestCase(BaseModel):
    input: str
    expected_output: str
    actual_output: str | None = None
    passed: bool | None = None
    score: float | None = None


class EvaluationAgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    total_tests: int
    passed_tests: int
    accuracy: float
    average_score: float
    average_latency_ms: float
    estimated_cost: float
    test_cases: list[EvaluationTestCase] = Field(default_factory=list)
    llm_reasoning: str | None = None
    llm_used: bool = False
    generated_at: datetime


class WorkflowRecommendation(BaseModel):
    title: str
    impact: SeverityLevel
    current_pattern: str
    suggested_pattern: str
    reason: str


class WorkflowEvolutionAgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    workflow_score: float
    severity: SeverityLevel
    recommendations: list[WorkflowRecommendation] = Field(default_factory=list)
    llm_reasoning: str | None = None
    llm_used: bool = False
    generated_at: datetime


class RootCauseEvidence(BaseModel):
    source: str
    description: str
    value: str | int | float | None = None


class RootCauseAgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    probable_root_cause: str
    confidence: float
    severity: SeverityLevel
    evidence: list[RootCauseEvidence] = Field(default_factory=list)
    recommended_fixes: list[str] = Field(default_factory=list)
    analyzed_failures: int
    llm_reasoning: str | None = None
    llm_used: bool = False
    generated_at: datetime


class OptimizationRecommendation(BaseModel):
    title: str
    impact: SeverityLevel
    description: str
    expected_savings_percent: float | None = None


class OptimizationAgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    total_cost: float
    average_cost: float
    average_latency_ms: float
    total_tokens: int
    recommendations: list[OptimizationRecommendation] = Field(default_factory=list)
    llm_reasoning: str | None = None
    llm_used: bool = False
    generated_at: datetime


class IncidentReportResponse(BaseModel):
    agent_id: str
    agent_name: str
    severity: SeverityLevel
    affected_executions: int
    summary: str
    probable_cause: str
    recommended_actions: list[str] = Field(default_factory=list)
    llm_reasoning: str | None = None
    llm_used: bool = False
    generated_at: datetime


class MultiAgentDiagnosticResponse(BaseModel):
    agent_id: str
    agent_name: str
    monitoring: MonitoringAgentResponse
    prompt_injection: PromptInjectionAgentResponse | None = None
    hallucination: HallucinationAgentResponse | None = None
    evaluation: EvaluationAgentResponse | None = None
    workflow_evolution: WorkflowEvolutionAgentResponse | None = None
    root_cause: RootCauseAgentResponse | None = None
    optimization: OptimizationAgentResponse | None = None
    incident: IncidentReportResponse | None = None
    final_summary: str
    executed_agents: list[str]
    llm_reasoning: str | None = None
    llm_used: bool = False
    autonomous_priority: SeverityLevel = "low"
    generated_at: datetime


class DiagnosticReportRecord(BaseModel):
    id: str
    user_id: str
    agent_id: str
    agent_name: str
    report_type: str
    payload: dict
    created_at: datetime


class AutoDiagnosticRunResponse(BaseModel):
    agents_scanned: int
    reports_created: int
    reports: list[MultiAgentDiagnosticResponse] = Field(default_factory=list)


class AlertResponse(BaseModel):
    id: str
    user_id: str
    agent_id: str
    agent_name: str
    title: str
    severity: SeverityLevel
    message: str
    source: str
    is_read: bool
    created_at: datetime


class SchedulerRunResponse(BaseModel):
    agents_scanned: int
    reports_created: int
    alerts_created: int
