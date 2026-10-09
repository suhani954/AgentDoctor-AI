from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ExecutionStatus = Literal["success", "failed", "running"]


class ToolCall(BaseModel):
    name: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] | str | None = None
    status: str = "success"
    duration_ms: int = 0


class TraceStep(BaseModel):
    step_type: str
    name: str
    content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime | None = None


class ExecutionCreateRequest(BaseModel):
    agent_id: str
    input: str = Field(..., min_length=1)
    output: str | None = None
    status: ExecutionStatus = "success"
    error_message: str | None = None
    latency_ms: int = Field(default=0, ge=0)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    cost: float = Field(default=0, ge=0)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    trace_steps: list[TraceStep] = Field(default_factory=list)


class ExecutionResponse(BaseModel):
    id: str
    user_id: str
    agent_id: str
    input: str
    output: str | None = None
    status: ExecutionStatus
    error_message: str | None = None
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    tool_calls: list[dict[str, Any]]
    trace_steps: list[dict[str, Any]]
    created_at: datetime | None = None

class FlightRecorderEvent(BaseModel):
    order: int
    event_type: str
    title: str
    content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FlightRecorderResponse(BaseModel):
    execution_id: str
    agent_id: str
    status: ExecutionStatus
    timeline: list[FlightRecorderEvent]