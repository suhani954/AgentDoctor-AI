from pydantic import BaseModel


class OverviewAnalyticsResponse(BaseModel):
    total_agents: int
    total_executions: int
    success_rate: float
    failure_rate: float
    total_cost: float
    average_latency_ms: float


class CostByAgent(BaseModel):
    agent_id: str
    agent_name: str
    total_cost: float
    total_tokens: int
    execution_count: int


class CostAnalyticsResponse(BaseModel):
    total_cost: float
    total_tokens: int
    cost_by_agent: list[CostByAgent]


class LatencyByAgent(BaseModel):
    agent_id: str
    agent_name: str
    average_latency_ms: float
    max_latency_ms: int
    execution_count: int


class LatencyAnalyticsResponse(BaseModel):
    average_latency_ms: float
    max_latency_ms: int
    latency_by_agent: list[LatencyByAgent]


class FailureByAgent(BaseModel):
    agent_id: str
    agent_name: str
    failed_executions: int
    total_executions: int
    failure_rate: float


class FailureAnalyticsResponse(BaseModel):
    total_failures: int
    failure_rate: float
    failures_by_agent: list[FailureByAgent]

class HealthScoreResponse(BaseModel):
    agent_id: str
    agent_name: str
    score: int
    grade: str
    reliability_score: float
    latency_score: float
    cost_efficiency_score: float
    failure_rate: float
    average_latency_ms: float
    average_cost: float
    total_executions: int
    reasons: list[str]