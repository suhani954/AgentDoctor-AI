from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.schemas.analytics_schema import (
    CostAnalyticsResponse,
    FailureAnalyticsResponse,
    HealthScoreResponse,
    LatencyAnalyticsResponse,
    OverviewAnalyticsResponse,
)
from app.schemas.auth_schema import UserResponse
from app.services.analytics_service import (
    get_agent_health_score,
    get_cost_analytics,
    get_failure_analytics,
    get_latency_analytics,
    get_overview_analytics,
)


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewAnalyticsResponse)
async def overview_analytics_route(
    current_user: UserResponse = Depends(get_current_user),
) -> OverviewAnalyticsResponse:
    return await get_overview_analytics(current_user.id)


@router.get("/cost", response_model=CostAnalyticsResponse)
async def cost_analytics_route(
    current_user: UserResponse = Depends(get_current_user),
) -> CostAnalyticsResponse:
    return await get_cost_analytics(current_user.id)


@router.get("/latency", response_model=LatencyAnalyticsResponse)
async def latency_analytics_route(
    current_user: UserResponse = Depends(get_current_user),
) -> LatencyAnalyticsResponse:
    return await get_latency_analytics(current_user.id)


@router.get("/failures", response_model=FailureAnalyticsResponse)
async def failure_analytics_route(
    current_user: UserResponse = Depends(get_current_user),
) -> FailureAnalyticsResponse:
    return await get_failure_analytics(current_user.id)


@router.get("/agents/{agent_id}/health", response_model=HealthScoreResponse)
async def agent_health_score_route(
    agent_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> HealthScoreResponse:
    return await get_agent_health_score(current_user.id, agent_id)