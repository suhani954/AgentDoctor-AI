from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status

from app.db.mongodb import get_database
from app.models.agent import agent_document, object_id_from_string, serialize_agent
from app.schemas.agent_schema import AgentCreateRequest, AgentResponse, AgentUpdateRequest


AGENT_COLLECTION = "agents"


async def create_agent(user_id: str, payload: AgentCreateRequest) -> AgentResponse:
    database = get_database()

    document = agent_document(
        user_id=user_id,
        name=payload.name.strip(),
        description=payload.description,
        model=payload.model,
        status=payload.status,
    )

    result = await database[AGENT_COLLECTION].insert_one(document)
    created_agent = await database[AGENT_COLLECTION].find_one({"_id": result.inserted_id})

    return AgentResponse(**serialize_agent(created_agent))


async def list_agents(user_id: str) -> list[AgentResponse]:
    database = get_database()

    cursor = database[AGENT_COLLECTION].find({"user_id": user_id}).sort("created_at", -1)
    agents = await cursor.to_list(length=100)

    return [AgentResponse(**serialize_agent(agent)) for agent in agents]


async def get_agent(user_id: str, agent_id: str) -> AgentResponse:
    database = get_database()

    try:
        object_id = object_id_from_string(agent_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid agent id",
        ) from exc

    agent = await database[AGENT_COLLECTION].find_one(
        {
            "_id": object_id,
            "user_id": user_id,
        }
    )

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    return AgentResponse(**serialize_agent(agent))


async def update_agent(
    user_id: str,
    agent_id: str,
    payload: AgentUpdateRequest,
) -> AgentResponse:
    database = get_database()

    try:
        object_id = object_id_from_string(agent_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid agent id",
        ) from exc

    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] is not None:
        update_data["name"] = update_data["name"].strip()

    update_data["updated_at"] = datetime.now(timezone.utc)

    result = await database[AGENT_COLLECTION].update_one(
        {
            "_id": object_id,
            "user_id": user_id,
        },
        {
            "$set": update_data,
        },
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    updated_agent = await database[AGENT_COLLECTION].find_one({"_id": object_id})
    return AgentResponse(**serialize_agent(updated_agent))


async def delete_agent(user_id: str, agent_id: str) -> dict[str, str]:
    database = get_database()

    try:
        object_id = object_id_from_string(agent_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid agent id",
        ) from exc

    result = await database[AGENT_COLLECTION].delete_one(
        {
            "_id": object_id,
            "user_id": user_id,
        }
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    return {"message": "Agent deleted successfully"}