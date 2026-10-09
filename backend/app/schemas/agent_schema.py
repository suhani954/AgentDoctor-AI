from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


AgentStatus = Literal["active", "inactive", "error"]


class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    model: str = Field(default="llama3.1:8b", min_length=2, max_length=100)
    status: AgentStatus = "active"


class AgentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    model: str | None = Field(default=None, min_length=2, max_length=100)
    status: AgentStatus | None = None


class AgentResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: str | None = None
    model: str
    status: AgentStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None