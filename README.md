# AgentDoctor AI

AgentDoctor AI is a full-stack **agentic AI observability and diagnostics platform** built to monitor, debug, and improve AI agent systems. It records agent executions, replays execution traces, runs multi-agent LLM diagnostics, detects reliability and safety risks, and generates actionable diagnostic reports.

The project is designed like an operations command center for AI agents. Instead of only showing raw logs, AgentDoctor AI uses specialized diagnostic agents to reason over failures, latency, cost, hallucination risk, prompt injection risk, workflow quality, and incident patterns.

## Key Highlights

- Multi-agent diagnostic workflow powered by LangGraph
- Local LLM reasoning with Ollama/Llama
- Execution logging with latency, cost, token usage, errors, tool calls, and trace steps
- Flight Recorder for step-by-step execution replay
- Full Diagnosis for one selected agent
- Auto Run for system-wide scans across all agents
- Scheduler-style monitoring with reports and alerts
- Diagnostic report history with clear/delete support
- Modern React dashboard with charts, metrics, and guide page
- JWT authentication and user-scoped data

## Tech Stack

### Frontend

- React
- Vite
- JavaScript
- CSS
- Axios
- Recharts
- Lucide React
- React Router

### Backend

- Python
- FastAPI
- REST APIs
- Pydantic
- JWT authentication
- Motor / PyMongo

### Database

- MongoDB

### AI and Agentic Layer

- LangGraph
- Ollama
- Llama model
- LLM reasoning
- Prompt engineering
- Multi-agent orchestration

## Project Purpose

AI agents can fail in many ways. They may hallucinate, call tools incorrectly, take too long, use too many tokens, produce unsafe responses, or fail silently inside a workflow. AgentDoctor AI was built to make those behaviors visible and explainable.

The platform helps users answer questions such as:

- Why did this agent fail?
- Which executions were slow or costly?
- Is there a prompt injection risk?
- Is the agent hallucinating?
- Which part of the workflow should be improved?
- What actions should be taken next?

## Core Features

### 1. Authentication

Users can sign up, log in, and access protected pages using JWT authentication. Each user's agents, executions, reports, and alerts are stored separately.

### 2. Dashboard

The dashboard provides a high-level overview of agent operations, including:

- Total agents
- Total executions
- Failure rate
- Latency trends
- Cost metrics
- Token usage
- Visual charts

### 3. Agent Management

Users can create and manage AI agents. Each agent includes details such as name, description, model, and status.

### 4. Execution Logging

The Executions page allows users to log AI agent runs with:

- Input
- Output
- Status
- Error message
- Latency
- Prompt tokens
- Completion tokens
- Total tokens
- Cost
- Tool calls
- Trace steps

This execution data becomes the foundation for the diagnostic workflow.

### 5. Flight Recorder

Flight Recorder replays an execution timeline step by step. It helps users inspect what happened inside an agent run.

Example timeline:

```text
User Input -> Planner -> Tool Call -> Trace Step -> Final Output / Error
```

This is useful for debugging tool failures, slow workflows, missing context, repeated tool calls, or unexpected outputs.

### 6. Diagnostics

The Diagnostics page is the main command center. It supports individual diagnostics, full multi-agent diagnosis, system-wide scans, scheduled scans, report history, and autonomous alerts.

## Diagnostic Agents

AgentDoctor AI uses multiple specialized diagnostic agents. Each agent focuses on a specific operational or safety concern.

### Monitoring Agent

Analyzes overall execution health:

- Total executions
- Failure rate
- Average latency
- Total cost
- Health insights
- Recommended actions

### Root Cause Agent

Investigates failed executions and identifies likely causes using:

- Error messages
- Failed trace steps
- Tool call failures
- Latency patterns
- Failure count

### Optimization Agent

Finds opportunities to reduce cost and improve performance:

- Token usage
- Average cost
- Average latency
- Repeated tool calls
- Prompt optimization
- Caching recommendations

### Prompt Injection Agent

Detects unsafe or malicious instruction patterns such as:

- Ignore previous instructions
- Reveal your system prompt
- Bypass safety
- Developer mode
- Pretend to be

### Hallucination Agent

Analyzes outputs for possible unreliable or unsupported responses.

### Evaluation Agent

Reviews quality and performance signals such as:

- Accuracy
- Passed tests
- Average score
- Estimated cost
- Latency

### Workflow Evolution Agent

Suggests improvements to the agent workflow, including:

- Better routing
- Retry logic
- Tool usage improvements
- Prompt compression
- Workflow simplification

### Incident Commander Agent

Generates incident-style summaries when serious failures are detected:

- Severity
- Affected executions
- Probable cause
- Recommended actions

## LangGraph Workflow

The diagnostic workflow is coordinated using LangGraph. The system does not rely on a single LLM call. Instead, it runs a structured multi-agent workflow.

Simplified flow:

```text
Monitoring Agent
       |
       v
Prompt Injection Agent
       |
       v
Hallucination Agent
       |
       v
Evaluation Agent
       |
       v
Workflow Evolution Agent
       |
       v
Conditional Routing
       |
       |-- Root Cause Agent
       |-- Optimization Agent
       |-- Incident Commander Agent
       |
       v
Final Diagnostic Summary
```

This makes the project agentic because different agents have specialized roles, work through a coordinated workflow, reason over shared execution context, and generate reports automatically.

## Diagnostic Modes

### Full Diagnosis

Runs a deep diagnostic workflow for one selected agent. This is useful when the user wants detailed analysis of a specific agent.

### Auto Run

Scans all agents immediately and displays a system-wide diagnostic summary. It also creates individual reports for each agent.

### Run Scheduler

Simulates scheduled background monitoring. It scans all agents, saves diagnostic reports, and generates alerts when risks are found.

## Reports and Alerts

Diagnostic reports are saved in history and can be reviewed later. Reports include:

- Agent name
- Report type
- Final summary
- LLM reasoning
- Priority
- Diagnostic payload
- Generated timestamp

Alerts are generated for important issues such as:

- High failure rate
- High latency
- Cost spike
- Prompt injection risk
- Hallucination risk

## Usage Flow

1. Sign up or log in.
2. Create one or more AI agents.
3. Log successful and failed executions.
4. Open Flight Recorder to replay execution timelines.
5. Run Full Diagnosis for one selected agent.
6. Run Auto Run to scan all agents.
7. Run Scheduler to simulate background monitoring.
8. Review diagnostic reports and alerts.
9. Clear old execution/report history when needed.

## Why This Project Is Agentic

AgentDoctor AI is not just a dashboard with an LLM call. It uses a coordinated multi-agent workflow where each diagnostic agent has a specialized responsibility. The system can inspect execution data, reason over failures, detect risks, generate reports, create alerts, and scan multiple agents autonomously.

Agentic capabilities include:

- Specialized diagnostic agents
- LangGraph workflow orchestration
- LLM-based reasoning
- Autonomous scans
- Scheduler-style monitoring
- Report and alert generation
- Execution trace analysis
- Conditional diagnostic routing

## Future Improvements

- Real background scheduling with Celery or APScheduler
- WebSocket progress updates for long diagnostics
- Docker setup for easier deployment
- Role-based access control
- More advanced evaluation datasets
- Export reports as PDF
- CI/CD pipeline
- Cloud deployment
- More model/provider options