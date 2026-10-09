from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.db.mongodb import get_database
from app.models.user import object_id_from_string, serialize_user, user_document
from app.schemas.auth_schema import AuthResponse, LoginRequest, SignupRequest, UserResponse


USER_COLLECTION = "users"


async def get_user_by_email(email: str) -> dict | None:
    database = get_database()
    return await database[USER_COLLECTION].find_one({"email": email.lower()})


async def get_user_by_id(user_id: str) -> dict | None:
    database = get_database()
    try:
        object_id = object_id_from_string(user_id)
    except ValueError:
        return None
    return await database[USER_COLLECTION].find_one({"_id": object_id})


async def signup_user(payload: SignupRequest) -> AuthResponse:
    existing_user = await get_user_by_email(payload.email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    database = get_database()
    document = user_document(
        name=payload.name.strip(),
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    result = await database[USER_COLLECTION].insert_one(document)
    created_user = await database[USER_COLLECTION].find_one({"_id": result.inserted_id})

    user = UserResponse(**serialize_user(created_user))
    return AuthResponse(access_token=create_access_token(user.id), user=user)


async def login_user(payload: LoginRequest) -> AuthResponse:
    user_document_from_db = await get_user_by_email(payload.email)
    if user_document_from_db is None or not verify_password(
        payload.password,
        user_document_from_db["hashed_password"],
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user_document_from_db.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    user = UserResponse(**serialize_user(user_document_from_db))
    return AuthResponse(access_token=create_access_token(user.id), user=user)
