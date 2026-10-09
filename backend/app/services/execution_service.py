from fastapi import HTTPException, status

from app.db.mongodb import get_database
from app.models.agent import object_id_from_string as agent_object_id_from_string
from app.models.execution import (
    execution_document,
    object_id_from_string,
    serialize_execution,
)
from app.schemas.execution_schema import (
    ExecutionCreateRequest, 
    ExecutionResponse, 
    FlightRecorderEvent, 
    FlightRecorderResponse,
)


AGENT_COLLECTION = "agents"
EXECUTION_COLLECTION = "executions"


async def ensure_agent_belongs_to_user(user_id: str, agent_id: str) -> None:
    database = get_database()

    try:
        object_id = agent_object_id_from_string(agent_id)
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


async def create_execution(
    user_id: str,
    payload: ExecutionCreateRequest,
) -> ExecutionResponse:
    database = get_database()

    await ensure_agent_belongs_to_user(user_id, payload.agent_id)

    total_tokens = payload.total_tokens
    if total_tokens == 0:
        total_tokens = payload.prompt_tokens + payload.completion_tokens

    document = execution_document(
        user_id=user_id,
        agent_id=payload.agent_id,
        input=payload.input,
        output=payload.output,
        status=payload.status,
        error_message=payload.error_message,
        latency_ms=payload.latency_ms,
        prompt_tokens=payload.prompt_tokens,
        completion_tokens=payload.completion_tokens,
        total_tokens=total_tokens,
        cost=payload.cost,
        tool_calls=[tool_call.model_dump() for tool_call in payload.tool_calls],
        trace_steps=[trace_step.model_dump() for trace_step in payload.trace_steps],
    )

    result = await database[EXECUTION_COLLECTION].insert_one(document)
    created_execution = await database[EXECUTION_COLLECTION].find_one(
        {"_id": result.inserted_id}
    )

    return ExecutionResponse(**serialize_execution(created_execution))


async def list_executions(user_id: str) -> list[ExecutionResponse]:
    database = get_database()

    cursor = (
        database[EXECUTION_COLLECTION]
        .find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(100)
    )
    executions = await cursor.to_list(length=100)

    return [ExecutionResponse(**serialize_execution(execution)) for execution in executions]


async def clear_executions(user_id: str) -> int:
    database = get_database()
    result = await database[EXECUTION_COLLECTION].delete_many({"user_id": user_id})
    return result.deleted_count


async def list_agent_executions(
    user_id: str,
    agent_id: str,
) -> list[ExecutionResponse]:
    database = get_database()

    await ensure_agent_belongs_to_user(user_id, agent_id)

    cursor = (
        database[EXECUTION_COLLECTION]
        .find(
            {
                "user_id": user_id,
                "agent_id": agent_id,
            }
        )
        .sort("created_at", -1)
        .limit(100)
    )
    executions = await cursor.to_list(length=100)

    return [ExecutionResponse(**serialize_execution(execution)) for execution in executions]


async def get_execution(user_id: str, execution_id: str) -> ExecutionResponse:
    database = get_database()

    try:
        object_id = object_id_from_string(execution_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid execution id",
        ) from exc

    execution = await database[EXECUTION_COLLECTION].find_one(
        {
            "_id": object_id,
            "user_id": user_id,
        }
    )

    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )

    return ExecutionResponse(**serialize_execution(execution))


async def get_flight_recorder(
    user_id: str,
    execution_id: str,
) -> FlightRecorderResponse:
    execution = await get_execution(user_id, execution_id)

    timeline: list[FlightRecorderEvent] = []
    order = 1

    timeline.append(
        FlightRecorderEvent(
            order=order,
            event_type="input",
            title="User Input",
            content=execution.input,
            metadata={},
        )
    )
    order += 1

    for trace_step in execution.trace_steps:
        timeline.append(
            FlightRecorderEvent(
                order=order,
                event_type=trace_step.get("step_type", "trace"),
                title=trace_step.get("name", "Trace Step"),
                content=trace_step.get("content"),
                metadata=trace_step.get("metadata", {}),
            )
        )
        order += 1

    for tool_call in execution.tool_calls:
        timeline.append(
            FlightRecorderEvent(
                order=order,
                event_type="tool_call",
                title=tool_call.get("name", "Tool Call"),
                content=str(tool_call.get("output")),
                metadata={
                    "input": tool_call.get("input", {}),
                    "status": tool_call.get("status", "unknown"),
                    "duration_ms": tool_call.get("duration_ms", 0),
                },
            )
        )
        order += 1

    if execution.output:
        timeline.append(
            FlightRecorderEvent(
                order=order,
                event_type="output",
                title="Final Output",
                content=execution.output,
                metadata={},
            )
        )
        order += 1

    if execution.error_message:
        timeline.append(
            FlightRecorderEvent(
                order=order,
                event_type="error",
                title="Execution Error",
                content=execution.error_message,
                metadata={},
            )
        )

    return FlightRecorderResponse(
        execution_id=execution.id,
        agent_id=execution.agent_id,
        status=execution.status,
        timeline=timeline,
    )
