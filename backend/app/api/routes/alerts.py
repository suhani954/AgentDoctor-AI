from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.schemas.auth_schema import UserResponse
from app.schemas.diagnostic_schema import AlertResponse
from app.services.alert_service import list_alerts


router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
async def list_alerts_route(
    current_user: UserResponse = Depends(get_current_user),
) -> list[AlertResponse]:
    return await list_alerts(current_user.id)