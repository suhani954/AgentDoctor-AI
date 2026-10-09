from datetime import datetime, timezone
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.agents.incident_commander_agent import run_incident_commander_agent
from app.agents.prompt_injection_agent import run_prompt_injection_agent
from app.agents.hallucination_agent import run_hallucination_agent
from app.agents.evaluation_agent import run_evaluation_agent
from app.agents.workflow_evolution_agent import run_workflow_evolution_agent
from app.agents.monitoring_agent import run_monitoring_agent
from app.agents.optimization_agent import run_optimization_agent
from app.agents.root_cause_agent import run_root_cause_agent

from app.schemas.diagnostic_schema import (
    IncidentReportResponse,
    PromptInjectionAgentResponse,
    HallucinationAgentResponse,
    EvaluationAgentResponse,
    WorkflowEvolutionAgentResponse,
    MonitoringAgentResponse,
    MultiAgentDiagnosticResponse,
    OptimizationAgentResponse,
    RootCauseAgentResponse,
)


class DiagnosticState(TypedDict, total=False):
    user_id: str
    agent_id: str
    agent_name: str
    prompt_injection: PromptInjectionAgentResponse
    hallucination: HallucinationAgentResponse
    evaluation: EvaluationAgentResponse
    workflow_evolution: WorkflowEvolutionAgentResponse
    monitoring: MonitoringAgentResponse
    root_cause: RootCauseAgentResponse
    optimization: OptimizationAgentResponse
    incident: IncidentReportResponse
    executed_agents: list[str]
    final_summary: str



async def prompt_injection_node(state: DiagnosticState) -> DiagnosticState:
    prompt_injection = await run_prompt_injection_agent(
        user_id=state["user_id"],
        agent_id=state["agent_id"],
    )

    executed_agents = state.get("executed_agents", [])
    executed_agents.append("Prompt Injection Detector")

    return {
        **state,
        "prompt_injection": prompt_injection,
        "executed_agents": executed_agents,
    }


async def hallucination_node(state: DiagnosticState) -> DiagnosticState:
    hallucination = await run_hallucination_agent(
        user_id=state["user_id"],
        agent_id=state["agent_id"],
    )

    executed_agents = state.get("executed_agents", [])
    executed_agents.append("Hallucination Investigator")

    return {
        **state,
        "hallucination": hallucination,
        "executed_agents": executed_agents,
    }



async def evaluation_node(state: DiagnosticState) -> DiagnosticState:
    evaluation = await run_evaluation_agent(
        user_id=state["user_id"],
        agent_id=state["agent_id"],
    )

    executed_agents = state.get("executed_agents", [])
    executed_agents.append("Evaluation Agent")

    return {
        **state,
        "evaluation": evaluation,
        "executed_agents": executed_agents,
    }



async def workflow_evolution_node(state: DiagnosticState) -> DiagnosticState:
    workflow_evolution = await run_workflow_evolution_agent(
        user_id=state["user_id"],
        agent_id=state["agent_id"],
    )

    executed_agents = state.get("executed_agents", [])
    executed_agents.append("Workflow Evolution Agent")

    return {
        **state,
        "workflow_evolution": workflow_evolution,
        "executed_agents": executed_agents,
    }


async def monitoring_node(state: DiagnosticState) -> DiagnosticState:
    monitoring = await run_monitoring_agent(
        user_id=state["user_id"],
        agent_id=state["agent_id"],
    )

    executed_agents = state.get("executed_agents", [])
    executed_agents.append("Monitoring Agent")

    return {
        **state,
        "agent_name": monitoring.agent_name,
        "monitoring": monitoring,
        "executed_agents": executed_agents,
    }


def route_after_monitoring(state: DiagnosticState) -> str:
    monitoring = state["monitoring"]

    has_failures = monitoring.failure_rate > 0
    has_optimization_issue = (
        monitoring.average_latency_ms >= 2500 or monitoring.total_cost >= 0.25
    )

    if has_failures:
        return "root_cause"

    if has_optimization_issue:
        return "optimization"

    return "summary"


async def root_cause_node(state: DiagnosticState) -> DiagnosticState:
    root_cause = await run_root_cause_agent(
        user_id=state["user_id"],
        agent_id=state["agent_id"],
    )

    executed_agents = state.get("executed_agents", [])
    executed_agents.append("Root Cause Analysis Agent")

    return {
        **state,
        "root_cause": root_cause,
        "executed_agents": executed_agents,
    }


def route_after_root_cause(state: DiagnosticState) -> str:
    monitoring = state["monitoring"]

    if monitoring.average_latency_ms >= 2500 or monitoring.total_cost >= 0.25:
        return "optimization"

    return "incident"


async def optimization_node(state: DiagnosticState) -> DiagnosticState:
    optimization = await run_optimization_agent(
        user_id=state["user_id"],
        agent_id=state["agent_id"],
    )

    executed_agents = state.get("executed_agents", [])
    executed_agents.append("Optimization Agent")

    return {
        **state,
        "optimization": optimization,
        "executed_agents": executed_agents,
    }


def route_after_optimization(state: DiagnosticState) -> str:
    monitoring = state["monitoring"]

    if monitoring.failure_rate > 0:
        return "incident"

    return "summary"


async def incident_node(state: DiagnosticState) -> DiagnosticState:
    incident = await run_incident_commander_agent(
        user_id=state["user_id"],
        agent_id=state["agent_id"],
    )

    executed_agents = state.get("executed_agents", [])
    executed_agents.append("Incident Commander Agent")

    return {
        **state,
        "incident": incident,
        "executed_agents": executed_agents,
    }


async def summary_node(state: DiagnosticState) -> DiagnosticState:
    monitoring = state["monitoring"]

    summary_parts = [
        f"Monitoring completed for {monitoring.agent_name}.",
        f"Failure rate: {monitoring.failure_rate}%.",
        f"Average latency: {monitoring.average_latency_ms} ms.",
        f"Total cost: {monitoring.total_cost}.",
    ]

    if state.get("root_cause"):
        summary_parts.append(
            f"Probable root cause: {state['root_cause'].probable_root_cause}."
        )

    if state.get("optimization"):
        summary_parts.append(
            f"Optimization recommendations: {len(state['optimization'].recommendations)}."
        )

    if state.get("incident"):
        summary_parts.append(
            f"Incident severity: {state['incident'].severity}."
        )

    return {
        **state,
        "final_summary": " ".join(summary_parts),
    }


def build_diagnostic_graph():
    graph = StateGraph(DiagnosticState)

    graph.add_node("prompt_injection", prompt_injection_node)
    graph.add_node("hallucination", hallucination_node)
    graph.add_node("evaluation", evaluation_node)
    graph.add_node("monitoring", monitoring_node)
    graph.add_node("workflow_evolution", workflow_evolution_node)
    graph.add_node("root_cause", root_cause_node)
    graph.add_node("optimization", optimization_node)
    graph.add_node("incident", incident_node)
    graph.add_node("summary", summary_node)

    graph.set_entry_point("monitoring")

    # graph.add_conditional_edges(
    #     "monitoring",
    #     route_after_monitoring,
    #     {
    #         "root_cause": "root_cause",
    #         "optimization": "optimization",
    #         "summary": "summary",
    #     },
    # )


    graph.add_edge("monitoring", "prompt_injection")
    # graph.add_conditional_edges(
    #     "prompt_injection",
    #     route_after_monitoring,
    #     {
    #         "root_cause": "root_cause",
    #         "optimization": "optimization",
    #         "summary": "summary",
    #     },
    # )

    graph.add_edge("prompt_injection", "hallucination")
    graph.add_edge("hallucination", "evaluation")
    graph.add_edge("evaluation", "workflow_evolution")
    # graph.add_conditional_edges(
    #     "hallucination",
    #     route_after_monitoring,
    #     {
    #         "root_cause": "root_cause",
    #         "optimization": "optimization",
    #         "summary": "summary",
    #     },
    # )


    # graph.add_conditional_edges(
    #     "evaluation",
    #     route_after_monitoring,
    #     {
    #         "root_cause": "root_cause",
    #         "optimization": "optimization",
    #         "summary": "summary",
    #     },
    # )


    graph.add_conditional_edges(
        "workflow_evolution",
        route_after_monitoring,
        {
            "root_cause": "root_cause",
            "optimization": "optimization",
            "summary": "summary",
        },
    )
    
    
    graph.add_conditional_edges(
        "root_cause",
        route_after_root_cause,
        {
            "optimization": "optimization",
            "incident": "incident",
        },
    )

    graph.add_conditional_edges(
        "optimization",
        route_after_optimization,
        {
            "incident": "incident",
            "summary": "summary",
        },
    )

    graph.add_edge("incident", "summary")
    graph.add_edge("summary", END)

    return graph.compile()


async def run_multi_agent_diagnostic(
    *,
    user_id: str,
    agent_id: str,
) -> MultiAgentDiagnosticResponse:
    diagnostic_graph = build_diagnostic_graph()

    result = await diagnostic_graph.ainvoke(
        {
            "user_id": user_id,
            "agent_id": agent_id,
            "executed_agents": [],
        }
    )

    return MultiAgentDiagnosticResponse(
        agent_id=agent_id,
        agent_name=result["agent_name"],
        monitoring=result["monitoring"],
        prompt_injection=result.get("prompt_injection"),
        hallucination=result.get("hallucination"),
        evaluation=result.get("evaluation"),
        workflow_evolution=result.get("workflow_evolution"),
        root_cause=result.get("root_cause"),
        optimization=result.get("optimization"),
        incident=result.get("incident"),
        final_summary=result["final_summary"],
        executed_agents=result.get("executed_agents", []),
        generated_at=datetime.now(timezone.utc),
    )