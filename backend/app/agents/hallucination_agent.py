from datetime import datetime, timezone
from typing import Any

from app.db.mongodb import get_database
from app.models.agent import object_id_from_string
from app.schemas.diagnostic_schema import (
    HallucinationAgentResponse,
    HallucinationFinding,
)
from app.services.llm_service import ask_ollama_json


AGENT_COLLECTION = "agents"
EXECUTION_COLLECTION = "executions"


RISKY_PHRASES = [
    "definitely",
    "guaranteed",
    "100%",
    "always",
    "never",
    "proven",
    "scientifically proven",
    "according to sources",
    "studies show",
    "experts say",
]


def severity_from_score(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def detect_basic_hallucination_risks(output: str) -> list[HallucinationFinding]:
    findings: list[HallucinationFinding] = []
    lower_output = output.lower()

    for phrase in RISKY_PHRASES:
        if phrase in lower_output:
            findings.append(
                HallucinationFinding(
                    claim=phrase,
                    reason="Output contains high-confidence or vague attribution language that may need verification.",
                    risk="medium",
                )
            )

    if len(output.split()) > 80 and not any(
        marker in lower_output for marker in ["source", "reference", "based on", "retrieved"]
    ):
        findings.append(
            HallucinationFinding(
                claim=output[:180],
                reason="Long answer does not mention retrieved evidence or source grounding.",
                risk="medium",
            )
        )

    return findings


def compact_output_context(executions: list[dict[str, Any]]) -> str:
    compact: list[dict[str, Any]] = []

    for execution in executions[:8]:
        compact.append(
            {
                "input": execution.get("input"),
                "output": execution.get("output"),
                "tool_calls": execution.get("tool_calls", [])[:2],
                "trace_steps": execution.get("trace_steps", [])[:3],
            }
        )

    return str(compact)


async def run_hallucination_agent(
    *,
    user_id: str,
    agent_id: str,
) -> HallucinationAgentResponse:
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

    successful_executions = await database[EXECUTION_COLLECTION].find(
        {
            "user_id": user_id,
            "agent_id": agent_id,
            "status": "success",
        }
    ).sort("created_at", -1).to_list(length=100)

    findings: list[HallucinationFinding] = []

    for execution in successful_executions:
        output = execution.get("output") or ""
        findings.extend(detect_basic_hallucination_risks(output))

    base_risk = min(100, len(findings) * 15)

    fallback = {
        "hallucination_risk": base_risk,
        "reasoning": (
            "Rule-based hallucination scan checked high-confidence language, vague attribution, "
            "and missing evidence signals."
        ),
        "findings": [finding.model_dump() for finding in findings[:10]],
        "recommended_actions": [
            "Require source grounding for factual answers.",
            "Add retrieval citations to agent outputs.",
            "Use evaluation datasets for high-risk domains.",
            "Flag high-confidence claims for review.",
        ],
    }

    llm_result, llm_used = await ask_ollama_json(
        system_prompt=(
            "You are a hallucination investigation agent for AI systems. "
            "Analyze outputs, inputs, tool calls, and trace steps for unsupported claims, "
            "overconfident language, missing evidence, or risky factual assertions. "
            "Return JSON with keys: hallucination_risk, reasoning, findings, recommended_actions. "
            "Each finding should have claim, reason, risk."
        ),
        user_prompt=(
            f"Agent name: {agent['name']}\n"
            f"Rule findings: {[finding.model_dump() for finding in findings[:10]]}\n"
            f"Recent successful execution context: {compact_output_context(successful_executions)}"
        ),
        fallback=fallback,
    )

    risk = llm_result.get("hallucination_risk", base_risk)

    try:
        risk = float(risk)
        if risk <= 1:
            risk *= 100
    except (TypeError, ValueError):
        risk = base_risk

    risk = min(max(risk, 0), 100)

    llm_findings = llm_result.get("findings", [])
    parsed_findings: list[HallucinationFinding] = []

    if isinstance(llm_findings, list):
        for item in llm_findings:
            if isinstance(item, dict):
                try:
                    parsed_findings.append(
                        HallucinationFinding(
                            claim=str(item.get("claim", "Potential unsupported claim")),
                            reason=str(item.get("reason", "Needs verification")),
                            risk=item.get("risk", severity_from_score(risk)),
                        )
                    )
                except Exception:
                    continue

    if parsed_findings:
        findings = parsed_findings

    recommended_actions = llm_result.get(
        "recommended_actions",
        fallback["recommended_actions"],
    )

    if not isinstance(recommended_actions, list):
        recommended_actions = [str(recommended_actions)]

    return HallucinationAgentResponse(
        agent_id=agent_id,
        agent_name=agent["name"],
        hallucination_risk=round(risk, 2),
        severity=severity_from_score(risk),
        findings=findings[:20],
        recommended_actions=recommended_actions,
        llm_reasoning=llm_result.get("reasoning"),
        llm_used=llm_used,
        generated_at=datetime.now(timezone.utc),
    )