from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.schemas.auth_schema import UserResponse
from app.schemas.diagnostic_schema import SchedulerRunResponse
from app.services.scheduler_service import run_scheduled_diagnostics_for_user


router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.post("/run", response_model=SchedulerRunResponse)
async def run_scheduler_route(
    current_user: UserResponse = Depends(get_current_user),
) -> SchedulerRunResponse:
    return await run_scheduled_diagnostics_for_user(current_user.id)