# from fastapi import APIRouter

# from app.api.routes.auth import router as auth_router
# from app.core.config import get_settings


# router = APIRouter()
# router.include_router(auth_router)


# @router.get("/health", tags=["health"])
# async def health_check() -> dict[str, str]:
#     settings = get_settings()
#     return {
#         "status": "healthy",
#         "app": settings.app_name,
#         "environment": settings.environment,
#     }

from fastapi import APIRouter

from app.api.routes.agents import router as agents_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.auth import router as auth_router
from app.api.routes.diagnostics import router as diagnostics_router
from app.api.routes.executions import router as executions_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.scheduler import router as scheduler_router
from app.core.config import get_settings


router = APIRouter()
router.include_router(auth_router)
router.include_router(agents_router)
router.include_router(executions_router)
router.include_router(analytics_router)
router.include_router(diagnostics_router)
router.include_router(alerts_router)
router.include_router(scheduler_router)


@router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.environment,
    }