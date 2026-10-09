from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user
from app.schemas.agent_schema import AgentCreateRequest, AgentResponse, AgentUpdateRequest
from app.schemas.auth_schema import UserResponse
from app.services.agent_service import (
    create_agent,
    delete_agent,
    get_agent,
    list_agents,
    update_agent,
)


router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_route(
    payload: AgentCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> AgentResponse:
    return await create_agent(current_user.id, payload)


@router.get("", response_model=list[AgentResponse])
async def list_agents_route(
    current_user: UserResponse = Depends(get_current_user),
) -> list[AgentResponse]:
    return await list_agents(current_user.id)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent_route(
    agent_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> AgentResponse:
    return await get_agent(current_user.id, agent_id)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent_route(
    agent_id: str,
    payload: AgentUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> AgentResponse:
    return await update_agent(current_user.id, agent_id, payload)


@router.delete("/{agent_id}")
async def delete_agent_route(
    agent_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> dict[str, str]:
    return await delete_agent(current_user.id, agent_id)