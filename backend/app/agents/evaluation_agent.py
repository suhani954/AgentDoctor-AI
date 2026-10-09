from datetime import datetime, timezone
from typing import Any

from app.db.mongodb import get_database
from app.models.agent import object_id_from_string
from app.schemas.diagnostic_schema import EvaluationAgentResponse, EvaluationTestCase
from app.services.llm_service import ask_ollama_json


AGENT_COLLECTION = "agents"
EXECUTION_COLLECTION = "executions"


DEFAULT_TEST_CASES = [
    EvaluationTestCase(
        input="Summarize a customer support issue clearly.",
        expected_output="A concise summary with the main problem and suggested next step.",
    ),
    EvaluationTestCase(
        input="Research a topic and return key points.",
        expected_output="A structured response with relevant facts and no unsupported claims.",
    ),
    EvaluationTestCase(
        input="Analyze an error log and explain the likely issue.",
        expected_output="A probable cause with evidence from the log.",
    ),
    EvaluationTestCase(
        input="Compare two options and recommend one.",
        expected_output="A balanced comparison with a justified recommendation.",
    ),
]


def estimate_similarity_score(expected: str, actual: str) -> float:
    expected_words = set(expected.lower().split())
    actual_words = set(actual.lower().split())

    if not expected_words or not actual_words:
        return 0

    overlap = expected_words.intersection(actual_words)
    return round((len(overlap) / len(expected_words)) * 100, 2)


def compact_execution_samples(executions: list[dict[str, Any]]) -> str:
    samples: list[dict[str, Any]] = []

    for execution in executions[:10]:
        samples.append(
            {
                "input": execution.get("input"),
                "output": execution.get("output"),
                "status": execution.get("status"),
                "latency_ms": execution.get("latency_ms"),
                "cost": execution.get("cost"),
            }
        )

    return str(samples)


async def run_evaluation_agent(
    *,
    user_id: str,
    agent_id: str,
) -> EvaluationAgentResponse:
    database = get_database()

    try:
        object_id = object_id_from_string(agent_id)
    except ValueError as exc:
        raise ValueError("Invalid agent id") from exc

    agent = await database[AGENT_COLLECTION].find_one(
        {
            "_id": object_id,
            "user_id": user_id,
        }
    )

    if agent is None:
        raise LookupError("Agent not found")

    executions = await database[EXECUTION_COLLECTION].find(
        {
            "user_id": user_id,
            "agent_id": agent_id,
            "status": "success",
        }
    ).sort("created_at", -1).to_list(length=50)

    test_cases = [case.model_copy() for case in DEFAULT_TEST_CASES]

    if executions:
        for index, test_case in enumerate(test_cases):
            sample = executions[index % len(executions)]
            actual_output = sample.get("output") or ""
            score = estimate_similarity_score(test_case.expected_output, actual_output)

            test_case.actual_output = actual_output
            test_case.score = score
            test_case.passed = score >= 35
    else:
        for test_case in test_cases:
            test_case.actual_output = "No successful executions available for evaluation."
            test_case.score = 0
            test_case.passed = False

    total_tests = len(test_cases)
    passed_tests = len([case for case in test_cases if case.passed])
    average_score = round(
        sum(case.score or 0 for case in test_cases) / total_tests,
        2,
    )
    accuracy = round((passed_tests / total_tests) * 100, 2) if total_tests else 0

    average_latency_ms = 0
    estimated_cost = 0

    if executions:
        average_latency_ms = round(
            sum(execution.get("latency_ms", 0) for execution in executions)
            / len(executions),
            2,
        )
        estimated_cost = round(
            sum(execution.get("cost", 0) for execution in executions[:total_tests]),
            6,
        )

    fallback = {
        "reasoning": "Evaluation used deterministic similarity scoring against default benchmark-style test cases.",
        "accuracy": accuracy,
        "average_score": average_score,
    }

    llm_result, llm_used = await ask_ollama_json(
        system_prompt=(
            "You are an AI evaluation agent. Review benchmark-style test cases, "
            "actual outputs, expected outputs, and execution samples. "
            "Assess whether the agent appears accurate and reliable. "
            "Return JSON with keys: reasoning, accuracy, average_score."
        ),
        user_prompt=(
            f"Agent name: {agent['name']}\n"
            f"Test cases: {[case.model_dump() for case in test_cases]}\n"
            f"Execution samples: {compact_execution_samples(executions)}"
        ),
        fallback=fallback,
    )

    llm_accuracy = llm_result.get("accuracy", accuracy)
    llm_average_score = llm_result.get("average_score", average_score)

    try:
        accuracy = float(llm_accuracy)
        if accuracy <= 1:
            accuracy *= 100
    except (TypeError, ValueError):
        pass

    try:
        average_score = float(llm_average_score)
        if average_score <= 1:
            average_score *= 100
    except (TypeError, ValueError):
        pass

    accuracy = min(max(accuracy, 0), 100)
    average_score = min(max(average_score, 0), 100)

    return EvaluationAgentResponse(
        agent_id=agent_id,
        agent_name=agent["name"],
        total_tests=total_tests,
        passed_tests=passed_tests,
        accuracy=round(accuracy, 2),
        average_score=round(average_score, 2),
        average_latency_ms=average_latency_ms,
        estimated_cost=estimated_cost,
        test_cases=test_cases,
        llm_reasoning=llm_result.get("reasoning"),
        llm_used=llm_used,
        generated_at=datetime.now(timezone.utc),
    )