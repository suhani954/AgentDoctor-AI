from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user
from app.schemas.auth_schema import AuthResponse, LoginRequest, SignupRequest, UserResponse
from app.services.auth_service import login_user, signup_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest) -> AuthResponse:
    return await signup_user(payload)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest) -> AuthResponse:
    return await login_user(payload)


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    return current_user
