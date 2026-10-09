import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bot,
  Brain,
  ClipboardList,
  Compass,
  GitBranch,
  HelpCircle,
  Route,
  SearchCode,
  ShieldCheck,
  Sparkles,
  Waypoints,
} from "lucide-react";

const workflowSteps = [
  {
    title: "Create Agents",
    description:
      "Register the AI agents you want to monitor, including their model, status, and purpose.",
  },
  {
    title: "Log Executions",
    description:
      "Store successful and failed runs with inputs, outputs, latency, cost, tokens, trace steps, and tool calls.",
  },
  {
    title: "Replay Behavior",
    description:
      "Use Flight Recorder to inspect what happened inside one execution from input to final output.",
  },
  {
    title: "Run Diagnostics",
    description:
      "Specialized diagnostic agents analyze failures, risk, cost, latency, hallucination, safety, and workflow quality.",
  },
  {
    title: "Review Reports",
    description:
      "Read saved reports, LLM reasoning, priorities, recommendations, and autonomous alerts.",
  },
];

const pageCards = [
  {
    icon: BarChart3,
    title: "Dashboard",
    description:
      "The operations overview. It shows health metrics, trends, cost, latency, failures, and high-level platform status.",
  },
  {
    icon: Bot,
    title: "Agents",
    description:
      "The place to create, update, and manage AI agents that AgentDoctor AI will monitor and diagnose.",
  },
  {
    icon: Activity,
    title: "Executions",
    description:
      "The execution log. Add agent runs, inspect performance details, and open Flight Recorder timelines.",
  },
  {
    icon: SearchCode,
    title: "Diagnostics",
    description:
      "The command center for Full Diagnosis, Auto Run, Scheduler scans, report history, LLM reasoning, and alerts.",
  },
  {
    icon: HelpCircle,
    title: "Guide",
    description:
      "This documentation page. Use it when you need to understand the platform, workflow, and navigation.",
  },
];

const diagnosticModes = [
  {
    title: "Full Diagnosis",
    purpose: "Deep investigation for one selected agent.",
    when: "Use it when you want detailed analysis of one specific agent.",
  },
  {
    title: "Auto Run",
    purpose: "Manual system-wide scan across all agents.",
    when: "Use it when you want an immediate health check of the whole agent fleet.",
  },
  {
    title: "Run Scheduler",
    purpose: "Simulated background monitoring across all agents.",
    when: "Use it to represent scheduled autonomous checks that create reports and alerts.",
  },
];

const userTypes = [
  "AI developers building agent workflows",
  "ML engineers monitoring LLM applications",
  "QA engineers testing agent reliability",
  "Product teams using AI assistants in real workflows",
  "Students building real agentic AI projects",
  "Teams tracking cost, latency, safety, and failures",
];

const firstRunSteps = [
  "Create an agent from the Agents page.",
  "Log a few successful and failed executions.",
  "Open Executions and replay one run with Flight Recorder.",
  "Go to Diagnostics and run Full Diagnosis for one agent.",
  "Run Auto Run to scan every agent together.",
  "Review Diagnostic Report History and Autonomous Alerts.",
];

const bestPractices = [
  "Log both successful and failed executions so diagnostics have contrast.",
  "Add realistic error messages when an execution fails.",
  "Include trace steps and tool calls for better Flight Recorder timelines.",
  "Review high-priority reports before low-priority ones.",
  "Clear old report and execution history when tables become too large.",
];

export default function Guide() {
  return (
    <div className="guide-page">
      <div className="page-heading guide-heading panel-card">
        <div>
          <div className="guide-heading-title">
            <HelpCircle size={22} />
            <h2>Guide</h2>
          </div>
          <p>
            Understand what AgentDoctor AI does, how each page works, and how
            to use the platform effectively.
          </p>
        </div>

        <div className="guide-heading-map" aria-hidden="true">
          <span>Agent</span>
          <i />
          <span>Diagnosis</span>
          <i />
          <span>Action</span>
        </div>
      </div>

      <section className="guide-hero panel-card">
        <div>
          <span className="guide-kicker">AgentDoctor AI</span>
          <h3>AI operations command center for agentic systems</h3>
          <p>
            AgentDoctor AI helps teams monitor AI agents, inspect execution
            behavior, diagnose failures, reason over risks with LLM-powered
            diagnostic agents, and generate actionable reports.
          </p>

          <div className="guide-hero-chips">
            <span>Failure analysis</span>
            <span>Prompt safety</span>
            <span>Cost control</span>
            <span>Workflow intelligence</span>
          </div>
        </div>

        <div className="guide-hero-metrics">
          <div>
            <strong>Multi-agent</strong>
            <span>Specialized diagnostic workflow</span>
          </div>
          <div>
            <strong>LLM reasoning</strong>
            <span>Natural explanations and fixes</span>
          </div>
          <div>
            <strong>Autonomous</strong>
            <span>Reports, alerts, and scheduled scans</span>
          </div>
        </div>
      </section>

      <section className="guide-cinema-panel panel-card">
        <div className="section-title">
          <Waypoints size={18} />
          <h3>Operating Loop</h3>
        </div>

        <div className="guide-loop">
          <div>
            <Bot size={22} />
            <strong>Agent Activity</strong>
            <p>Executions, tool calls, costs, traces, and failures are captured.</p>
          </div>
          <span />
          <div>
            <Brain size={22} />
            <strong>LLM Diagnosis</strong>
            <p>Specialist agents reason over telemetry and generate explanations.</p>
          </div>
          <span />
          <div>
            <ShieldCheck size={22} />
            <strong>Operational Action</strong>
            <p>Reports, priorities, fixes, and alerts guide the next decision.</p>
          </div>
        </div>
      </section>

      <section className="guide-grid overview">
        <div className="panel-card guide-section guide-compact-section pastel mint">
          <div className="section-title">
            <Compass size={18} />
            <h3>Purpose</h3>
          </div>
          <p>
            The platform is built to make AI agents easier to operate in real
            conditions. It tracks what agents do, detects reliability and safety
            problems, explains likely causes, and recommends next actions before
            small issues become bigger incidents.
          </p>
          <div className="guide-purpose-chips">
            <span>Observe</span>
            <span>Diagnose</span>
            <span>Improve</span>
          </div>
        </div>

        <div className="panel-card guide-section pastel lavender">
          <div className="section-title">
            <ShieldCheck size={18} />
            <h3>Who Can Use It</h3>
          </div>
          <ul className="guide-list compact">
            {userTypes.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="panel-card guide-section pastel peach">
        <div className="section-title">
          <GitBranch size={18} />
          <h3>How It Works</h3>
        </div>

        <div className="guide-timeline">
          {workflowSteps.map((step, index) => (
            <div className="guide-timeline-item" key={step.title}>
              <span>{index + 1}</span>
              <div>
                <strong>{step.title}</strong>
                <p>{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="panel-card guide-section pastel sky">
        <div className="section-title">
          <Route size={18} />
          <h3>Pages Explained</h3>
        </div>

        <div className="guide-card-grid">
          {pageCards.map((page) => {
            const Icon = page.icon;

            return (
              <article className="guide-page-card" key={page.title}>
                <Icon size={20} />
                <h4>{page.title}</h4>
                <p>{page.description}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="panel-card guide-section pastel butter">
        <div className="section-title">
          <Brain size={18} />
          <h3>Diagnostic Modes</h3>
        </div>

        <div className="guide-mode-grid">
          {diagnosticModes.map((mode) => (
            <article className="guide-mode-card" key={mode.title}>
              <h4>{mode.title}</h4>
              <strong>{mode.purpose}</strong>
              <p>{mode.when}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="guide-grid two">
        <div className="panel-card guide-section pastel rose">
          <div className="section-title">
            <ClipboardList size={18} />
            <h3>First-Time Path</h3>
          </div>
          <ol className="guide-list numbered">
            {firstRunSteps.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </div>

        <div className="panel-card guide-section pastel aqua">
          <div className="section-title">
            <Sparkles size={18} />
            <h3>Agentic AI Layer</h3>
          </div>
          <p>
            AgentDoctor AI uses specialized diagnostic agents for monitoring,
            prompt injection, hallucination, evaluation, workflow evolution,
            root cause analysis, optimization, and incident reporting. These
            agents collaborate through a diagnostic workflow and use LLM
            reasoning to produce explanations and recommendations.
          </p>
        </div>
      </section>

      <section className="panel-card guide-section pastel mint">
        <div className="section-title">
          <AlertTriangle size={18} />
          <h3>Best Practices</h3>
        </div>
        <ul className="guide-list best-practices">
          {bestPractices.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
