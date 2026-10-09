import asyncio
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.core.config import get_settings
from app.core.security import hash_password


DEMO_EMAIL = "demo@agentdoctor.ai"
DEMO_PASSWORD = "AgentDoctorDemo@2026#LocalOnly"

AGENT_COLLECTION = "agents"
EXECUTION_COLLECTION = "executions"
USER_COLLECTION = "users"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def random_created_at(days_back: int = 14) -> datetime:
    return now_utc() - timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )


def make_tool_call(
    name: str,
    status: str = "success",
    duration_ms: int | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "input": {
            "query": f"sample input for {name}",
        },
        "output": {
            "result": f"sample output from {name}",
        }
        if status == "success"
        else {
            "error": f"{name} failed during execution",
        },
        "status": status,
        "duration_ms": duration_ms or random.randint(200, 1800),
    }


def make_trace_steps(
    *,
    model: str,
    failed: bool,
    tool_name: str,
) -> list[dict[str, Any]]:
    steps = [
        {
            "step_type": "llm",
            "name": "planner",
            "content": "Created an execution plan for the user request.",
            "metadata": {
                "model": model,
            },
            "timestamp": random_created_at().isoformat(),
        },
        {
            "step_type": "tool",
            "name": tool_name,
            "content": f"Called {tool_name} to gather supporting information.",
            "metadata": {
                "duration_ms": random.randint(300, 1500),
            },
            "timestamp": random_created_at().isoformat(),
        },
    ]

    if failed:
        steps.append(
            {
                "step_type": "error",
                "name": "execution_error",
                "content": "Execution failed before final response generation.",
                "metadata": {
                    "recoverable": True,
                },
                "timestamp": random_created_at().isoformat(),
            }
        )
    else:
        steps.append(
            {
                "step_type": "llm",
                "name": "final_response",
                "content": "Generated final response from gathered context.",
                "metadata": {
                    "model": model,
                },
                "timestamp": random_created_at().isoformat(),
            }
        )

    return steps


def make_execution(
    *,
    user_id: str,
    agent_id: str,
    model: str,
    behavior: str,
) -> dict[str, Any]:
    failed = behavior == "failed"
    slow = behavior == "slow"
    expensive = behavior == "expensive"

    tool_name = random.choice(["web_search", "retriever", "database_lookup", "calculator"])

    latency_ms = random.randint(800, 2200)

    if slow:
        latency_ms = random.randint(5500, 13000)

    prompt_tokens = random.randint(250, 900)
    completion_tokens = random.randint(120, 500)

    if expensive:
        prompt_tokens = random.randint(2500, 6000)
        completion_tokens = random.randint(900, 2200)

    total_tokens = prompt_tokens + completion_tokens

    cost = round(total_tokens * 0.000003, 6)

    if expensive:
        cost = round(total_tokens * 0.00001, 6)

    error_message = None

    if failed:
        error_message = random.choice(
            [
                "Tool execution failed: retriever returned invalid response",
                "Database timeout while reading vector index",
                "Rate limit exceeded: 429 from model provider",
                "Execution timed out after 30 seconds",
                "Token context limit exceeded during response generation",
            ]
        )

    tool_status = "failed" if failed and random.random() > 0.35 else "success"

    created_at = random_created_at()

    return {
        "user_id": user_id,
        "agent_id": agent_id,
        "input": random.choice(
            [
                "Research the latest trends in AI agents.",
                "Summarize the uploaded document.",
                "Find pricing information and compare options.",
                "Generate a support response for the customer issue.",
                "Analyze logs and explain the failure.",
            ]
        ),
        "output": None
        if failed
        else random.choice(
            [
                "Completed the task successfully with supporting details.",
                "Generated a concise answer based on available context.",
                "Returned a structured response with recommendations.",
                "Completed analysis and produced final output.",
            ]
        ),
        "status": "failed" if failed else "success",
        "error_message": error_message,
        "latency_ms": latency_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost": cost,
        "tool_calls": [
            make_tool_call(
                tool_name,
                status=tool_status,
                duration_ms=random.randint(300, latency_ms),
            )
        ],
        "trace_steps": make_trace_steps(
            model=model,
            failed=failed,
            tool_name=tool_name,
        ),
        "created_at": created_at,
    }


async def seed_demo_data() -> None:
    load_dotenv(ROOT_DIR / ".env")

    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_url)
    database = client[settings.mongodb_db_name]

    existing_user = await database[USER_COLLECTION].find_one({"email": DEMO_EMAIL})

    if existing_user:
        user_id = str(existing_user["_id"])
        await database[USER_COLLECTION].update_one(
            {"_id": existing_user["_id"]},
            {
                "$set": {
                    "hashed_password": hash_password(DEMO_PASSWORD),
                    "updated_at": now_utc(),
                }
            },
        )
        print(f"Updated existing demo user password: {DEMO_EMAIL}")
    else:
        now = now_utc()
        result = await database[USER_COLLECTION].insert_one(
            {
                "name": "Demo User",
                "email": DEMO_EMAIL,
                "hashed_password": hash_password(DEMO_PASSWORD),
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
        )
        user_id = str(result.inserted_id)
        print(f"Created demo user: {DEMO_EMAIL}")


    await database[AGENT_COLLECTION].delete_many({"user_id": user_id})
    await database[EXECUTION_COLLECTION].delete_many({"user_id": user_id})

    agent_configs = [
        {
            "name": "Research Agent",
            "description": "Performs web and document research workflows.",
            "model": "llama3.1:8b",
            "status": "active",
            "behaviors": ["success"] * 18 + ["slow"] * 5 + ["failed"] * 4,
        },
        {
            "name": "Support Agent",
            "description": "Handles support response generation and ticket triage.",
            "model": "llama3.2:3b",
            "status": "active",
            "behaviors": ["success"] * 20 + ["failed"] * 8 + ["slow"] * 3,
        },
        {
            "name": "Analysis Agent",
            "description": "Analyzes logs, metrics, and operational data.",
            "model": "llama3.1:8b",
            "status": "active",
            "behaviors": ["success"] * 15 + ["expensive"] * 8 + ["failed"] * 3,
        },
    ]

    created_agents = []

    for config in agent_configs:
        now = now_utc()
        result = await database[AGENT_COLLECTION].insert_one(
            {
                "user_id": user_id,
                "name": config["name"],
                "description": config["description"],
                "model": config["model"],
                "status": config["status"],
                "created_at": now,
                "updated_at": now,
            }
        )

        agent_id = str(result.inserted_id)
        created_agents.append((agent_id, config))

    execution_documents = []

    for agent_id, config in created_agents:
        for behavior in config["behaviors"]:
            execution_documents.append(
                make_execution(
                    user_id=user_id,
                    agent_id=agent_id,
                    model=config["model"],
                    behavior=behavior,
                )
            )

    random.shuffle(execution_documents)

    if execution_documents:
        await database[EXECUTION_COLLECTION].insert_many(execution_documents)

    print("")
    print("Seed demo data complete.")
    print(f"Demo email: {DEMO_EMAIL}")
    print(f"Demo password: {DEMO_PASSWORD}")
    print(f"Agents created: {len(created_agents)}")
    print(f"Executions created: {len(execution_documents)}")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
