from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user
from app.schemas.auth_schema import UserResponse
from app.schemas.execution_schema import (
    ExecutionCreateRequest, 
    ExecutionResponse, 
    FlightRecorderResponse,
)

from app.services.execution_service import (
    clear_executions,
    create_execution,
    get_execution,
    get_flight_recorder,
    list_agent_executions,
    list_executions,
)


router = APIRouter(tags=["executions"])


@router.post(
    "/executions",
    response_model=ExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_execution_route(
    payload: ExecutionCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> ExecutionResponse:
    return await create_execution(current_user.id, payload)


@router.get("/executions", response_model=list[ExecutionResponse])
async def list_executions_route(
    current_user: UserResponse = Depends(get_current_user),
) -> list[ExecutionResponse]:
    return await list_executions(current_user.id)


@router.delete("/executions")
async def clear_executions_route(
    current_user: UserResponse = Depends(get_current_user),
) -> dict[str, int]:
    deleted_count = await clear_executions(current_user.id)
    return {"deleted_count": deleted_count}


@router.get(
    "/executions/{execution_id}/flight-recorder",
    response_model=FlightRecorderResponse,
)
async def get_flight_recorder_route(
    execution_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> FlightRecorderResponse:
    return await get_flight_recorder(current_user.id, execution_id)



@router.get("/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution_route(
    execution_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ExecutionResponse:
    return await get_execution(current_user.id, execution_id)


@router.get("/agents/{agent_id}/executions", response_model=list[ExecutionResponse])
async def list_agent_executions_route(
    agent_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> list[ExecutionResponse]:
    return await list_agent_executions(current_user.id, agent_id)
