// export default function Diagnostics() {
//   return <h2>Diagnostics</h2>;
// }

// import {
//   Activity,
//   AlertTriangle,
//   Brain,
//   Bug,
//   CheckCircle2,
//   RefreshCw,
//   SearchCode,
//   Zap,
// } from "lucide-react";

import {
  Activity,
  AlertTriangle,
  Brain,
  Bug,
  FlaskConical,
  RefreshCw,
  SearchCode,
  ShieldAlert,
  Sparkles,
  Trash2,
  Workflow,
  Zap,
} from "lucide-react";

import { useEffect, useState } from "react";
import StatusBadge from "../components/common/StatusBadge";
import { getAgents } from "../services/agentService";
import { getAlerts } from "../services/alertService";
import { runScheduler } from "../services/schedulerService";
import { formatIndiaDateTime } from "../utils/date";
// import {
//   getDiagnosticReports,
//   runAutoDiagnostics,
//   runFullDiagnostic,
//   runIncidentDiagnostic,
//   runMonitoringDiagnostic,
//   runOptimizationDiagnostic,
//   runRootCauseDiagnostic,
// } from "../services/diagnosticService";


import {
  clearDiagnosticReports,
  getDiagnosticReports,
  runAutoDiagnostics,
  runEvaluationDiagnostic,
  runFullDiagnostic,
  runHallucinationDiagnostic,
  runIncidentDiagnostic,
  runMonitoringDiagnostic,
  runOptimizationDiagnostic,
  runPromptInjectionDiagnostic,
  runRootCauseDiagnostic,
  runWorkflowEvolutionDiagnostic,
} from "../services/diagnosticService";


// const diagnosticActions = [
//   {
//     key: "monitoring",
//     label: "Monitoring",
//     icon: Activity,
//     runner: runMonitoringDiagnostic,
//   },
//   {
//     key: "rootCause",
//     label: "Root Cause",
//     icon: Bug,
//     runner: runRootCauseDiagnostic,
//   },
//   {
//     key: "optimization",
//     label: "Optimization",
//     icon: Zap,
//     runner: runOptimizationDiagnostic,
//   },
//   {
//     key: "incident",
//     label: "Incident",
//     icon: AlertTriangle,
//     runner: runIncidentDiagnostic,
//   },
//   {
//     key: "full",
//     label: "Full Diagnosis",
//     icon: Brain,
//     runner: runFullDiagnostic,
//   },
// ];

const diagnosticActions = [
  {
    key: "monitoring",
    label: "Monitoring",
    icon: Activity,
    runner: runMonitoringDiagnostic,
  },
  {
    key: "promptInjection",
    label: "Prompt Injection",
    icon: ShieldAlert,
    runner: runPromptInjectionDiagnostic,
  },
  {
    key: "hallucination",
    label: "Hallucination",
    icon: Sparkles,
    runner: runHallucinationDiagnostic,
  },
  {
    key: "evaluation",
    label: "Evaluation",
    icon: FlaskConical,
    runner: runEvaluationDiagnostic,
  },
  {
    key: "rootCause",
    label: "Root Cause",
    icon: Bug,
    runner: runRootCauseDiagnostic,
  },
  {
    key: "optimization",
    label: "Optimization",
    icon: Zap,
    runner: runOptimizationDiagnostic,
  },
  {
    key: "workflowEvolution",
    label: "Workflow Evolution",
    icon: Workflow,
    runner: runWorkflowEvolutionDiagnostic,
  },
  {
    key: "incident",
    label: "Incident",
    icon: AlertTriangle,
    runner: runIncidentDiagnostic,
  },
  {
    key: "full",
    label: "Full Diagnosis",
    icon: Brain,
    runner: runFullDiagnostic,
  },
];

function formatCost(value) {
  return `$${Number(value || 0).toFixed(4)}`;
}

function formatPercent(value) {
  return `${Number(value || 0).toFixed(1)}%`;
}

function formatLatency(value) {
  return `${Math.round(value || 0)} ms`;
}

function getErrorMessage(error, fallback) {
  const detail = error?.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail) && detail[0]?.msg) {
    return detail[0].msg;
  }

  return fallback;
}

function formatIndiaTime(value) {
  return formatIndiaDateTime(value);
}

function ResultMetric({ label, value }) {
  return (
    <div className="result-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function InsightList({ title, items }) {
  if (!items?.length) return null;

  return (
    <div className="result-card">
      <h4>{title}</h4>
      <ul className="insight-list">
        {items.map((item, index) => (
          <li key={`${item.title || item.description || item}-${index}`}>
            {typeof item === "string" ? (
              <p>{item}</p>
            ) : (
              <>
                <strong>{item.title || item.source || "Insight"}</strong>
                <p>{item.description || item.value}</p>
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function RecommendationList({ title, items }) {
  if (!items?.length) return null;

  return (
    <div className="result-card">
      <h4>{title}</h4>
      <ul className="recommendation-list">
        {items.map((item, index) => (
          <li key={`${item.title || item}-${index}`}>
            {typeof item === "string" ? (
              <p>{item}</p>
            ) : (
              <>
                <strong>{item.title}</strong>
                <p>{item.description}</p>
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function getReportMetrics(report) {
  const monitoring = report.monitoring || {};
  const incident = report.incident;
  const rootCause = report.root_cause;

  return {
    executions: monitoring.total_executions ?? incident?.affected_executions ?? 0,
    failureRate: monitoring.failure_rate ?? 0,
    averageLatency: monitoring.average_latency_ms ?? 0,
    totalCost: monitoring.total_cost ?? 0,
    severity: incident?.severity || rootCause?.severity || "low",
    priority: report.autonomous_priority || "low",
    llmUsed: Boolean(
      report.llm_used ||
        report.monitoring?.llm_used ||
        report.root_cause?.llm_used ||
        report.optimization?.llm_used ||
        report.incident?.llm_used ||
        report.prompt_injection?.llm_used ||
        report.hallucination?.llm_used ||
        report.evaluation?.llm_used ||
        report.workflow_evolution?.llm_used
    ),
  };
}

function AutoRunReport({ result, onSelectReport }) {
  const reports = result.reports || [];
  const totalExecutions = reports.reduce(
    (total, report) => total + getReportMetrics(report).executions,
    0
  );
  const totalCost = reports.reduce(
    (total, report) => total + getReportMetrics(report).totalCost,
    0
  );
  const llmReports = reports.filter(
    (report) => getReportMetrics(report).llmUsed
  ).length;
  const highPriorityReports = reports.filter((report) =>
    ["high", "critical"].includes(getReportMetrics(report).priority)
  ).length;

  return (
    <div className="diagnostic-result-stack">
      <div className="summary-box">
        <strong>System-Wide Auto Run Summary</strong>
        <p>
          Auto Run scanned {result.agents_scanned} agents and created{" "}
          {result.reports_created} diagnostic reports.
        </p>
      </div>

      <div className="result-card">
        <h4>Fleet Snapshot</h4>
        <div className="result-grid">
          <ResultMetric label="Agents Scanned" value={result.agents_scanned} />
          <ResultMetric label="Reports Created" value={result.reports_created} />
          <ResultMetric label="Executions Reviewed" value={totalExecutions} />
          <ResultMetric label="Total Cost" value={formatCost(totalCost)} />
          <ResultMetric label="LLM Reports" value={llmReports} />
          <ResultMetric label="High Priority" value={highPriorityReports} />
        </div>
      </div>

      <div className="auto-run-report-list">
        {reports.map((report) => {
          const metrics = getReportMetrics(report);

          return (
            <button
              className="auto-run-report-item"
              key={report.agent_id}
              onClick={() => onSelectReport(report)}
              type="button"
            >
              <div>
                <strong>{report.agent_name}</strong>
                <p>{report.final_summary}</p>
              </div>

              <div className="auto-run-report-metrics">
                <span>{metrics.priority} priority</span>
                <span>{formatPercent(metrics.failureRate)} failures</span>
                <span>{formatLatency(metrics.averageLatency)}</span>
                <span>{metrics.llmUsed ? "LLM used" : "LLM fallback"}</span>
              </div>
            </button>
          );
        })}
      </div>

      <details className="raw-result">
        <summary>Raw auto-run response</summary>
        <pre className="json-block">{JSON.stringify(result, null, 2)}</pre>
      </details>
    </div>
  );
}

function DiagnosticReport({ result }) {
  if (!result) return null;

  const report = result.monitoring || result;
  const rootCause = result.root_cause || result.probable_root_cause ? result.root_cause || result : null;
  const optimization = result.optimization || result.recommendations ? result.optimization || result : null;
  const incident = result.incident || result.affected_executions !== undefined ? result.incident || result : null;

  return (
    <div className="diagnostic-result-stack">
      {result.final_summary && (
        <div className="summary-box">
          <strong>Final Summary</strong>
          <p>{result.final_summary}</p>
        </div>
      )}

      {result.executed_agents && (
        <div className="executed-agents">
          {result.executed_agents.map((agentName) => (
            <span key={agentName}>{agentName}</span>
          ))}
        </div>
      )}

      <div className="result-card">
        <h4>Operational Snapshot</h4>
        <div className="result-grid">
          <ResultMetric
            label="Agent"
            value={report.agent_name || result.agent_name}
          />
          <ResultMetric
            label="Executions"
            value={
              report.total_executions ?? incident?.affected_executions ?? "-"
            }
          />
          <ResultMetric
            label="Failure Rate"
            value={
              report.failure_rate !== undefined
                ? formatPercent(report.failure_rate)
                : "-"
            }
          />
          <ResultMetric
            label="Avg Latency"
            value={
              report.average_latency_ms !== undefined
                ? formatLatency(report.average_latency_ms)
                : optimization?.average_latency_ms !== undefined
                  ? formatLatency(optimization.average_latency_ms)
                  : "-"
            }
          />
          <ResultMetric
            label="Total Cost"
            value={
              report.total_cost !== undefined
                ? formatCost(report.total_cost)
                : optimization?.total_cost !== undefined
                  ? formatCost(optimization.total_cost)
                  : "-"
            }
          />
          <ResultMetric
            label="Severity"
            value={incident?.severity || rootCause?.severity || "low"}
          />
          <ResultMetric
            label="Priority"
            value={result.autonomous_priority || "low"}
          />
        </div>
      </div>

      {rootCause && (
        <div className="result-card">
          <h4>Root Cause</h4>
          <div className="result-grid">
            <ResultMetric
              label="Probable Cause"
              value={rootCause.probable_root_cause}
            />
            <ResultMetric
              label="Confidence"
              value={`${rootCause.confidence}%`}
            />
            <ResultMetric
              label="Failures Analyzed"
              value={rootCause.analyzed_failures}
            />
          </div>
        </div>
      )}

      {incident && incident.summary && (
        <div className="result-card">
          <h4>Incident Report</h4>
          <p className="muted-text">{incident.summary}</p>
        </div>
      )}

      <InsightList
        title="Insights"
        items={report.insights || rootCause?.evidence}
      />
      <RecommendationList
        title="Recommended Actions"
        items={
          report.recommended_actions ||
          optimization?.recommendations ||
          incident?.recommended_actions ||
          rootCause?.recommended_fixes
        }
      />

      {(result.llm_reasoning ||
        result.monitoring?.llm_reasoning ||
        result.root_cause?.llm_reasoning ||
        result.optimization?.llm_reasoning ||
        result.incident?.llm_reasoning ||
        result.prompt_injection?.llm_reasoning ||
        result.hallucination?.llm_reasoning ||
        result.evaluation?.llm_reasoning ||
        result.workflow_evolution?.llm_reasoning) && (
        <div className="result-card llm-card">
          <h4>LLM Reasoning</h4>

          <div className="llm-status-row">
            <span>
              LLM Used:
              <strong>
                {result.llm_used ||
                result.monitoring?.llm_used ||
                result.root_cause?.llm_used ||
                result.optimization?.llm_used ||
                result.incident?.llm_used ||
                result.prompt_injection?.llm_used ||
                result.hallucination?.llm_used ||
                result.evaluation?.llm_used ||
                result.workflow_evolution?.llm_used
                  ? " Yes"
                  : " No"}
              </strong>
            </span>
          </div>

          <p>
            {result.llm_reasoning ||
              result.monitoring?.llm_reasoning ||
              result.root_cause?.llm_reasoning ||
              result.optimization?.llm_reasoning ||
              result.incident?.llm_reasoning ||
              result.prompt_injection?.llm_reasoning ||
              result.hallucination?.llm_reasoning ||
              result.evaluation?.llm_reasoning ||
              result.workflow_evolution?.llm_reasoning}
          </p>
        </div>
      )}

      {result.prompt_injection && (
        <div className="result-card">
          <h4>Prompt Injection</h4>
          <div className="result-grid">
            <ResultMetric
              label="Risk Score"
              value={`${result.prompt_injection.risk_score}%`}
            />
            <ResultMetric
              label="Severity"
              value={result.prompt_injection.severity}
            />
            <ResultMetric
              label="Findings"
              value={result.prompt_injection.findings?.length || 0}
            />
          </div>
        </div>
      )}

      {result.hallucination && (
        <div className="result-card">
          <h4>Hallucination</h4>
          <div className="result-grid">
            <ResultMetric
              label="Risk"
              value={`${result.hallucination.hallucination_risk}%`}
            />
            <ResultMetric
              label="Severity"
              value={result.hallucination.severity}
            />
            <ResultMetric
              label="Findings"
              value={result.hallucination.findings?.length || 0}
            />
          </div>
        </div>
      )}

      {result.evaluation && (
        <div className="result-card">
          <h4>Evaluation</h4>
          <div className="result-grid">
            <ResultMetric
              label="Accuracy"
              value={`${result.evaluation.accuracy}%`}
            />
            <ResultMetric
              label="Passed"
              value={`${result.evaluation.passed_tests}/${result.evaluation.total_tests}`}
            />
            <ResultMetric
              label="Avg Score"
              value={`${result.evaluation.average_score}%`}
            />
          </div>
        </div>
      )}

      {result.workflow_evolution && (
        <div className="result-card">
          <h4>Workflow Evolution</h4>
          <div className="result-grid">
            <ResultMetric
              label="Workflow Score"
              value={`${result.workflow_evolution.workflow_score}%`}
            />
            <ResultMetric
              label="Severity"
              value={result.workflow_evolution.severity}
            />
            <ResultMetric
              label="Recommendations"
              value={result.workflow_evolution.recommendations?.length || 0}
            />
          </div>
        </div>
      )}

      <details className="raw-result">
        <summary>Raw response</summary>
        <pre className="json-block">{JSON.stringify(result, null, 2)}</pre>
      </details>
    </div>
  );
}

export default function Diagnostics() {
  const [agents, setAgents] = useState([]);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [activeResult, setActiveResult] = useState(null);
  const [activeType, setActiveType] = useState("");
  const [loadingAgents, setLoadingAgents] = useState(true);
  const [running, setRunning] = useState("");
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [reports, setReports] = useState([]);
  const [autoRunning, setAutoRunning] = useState(false); 
  const [alerts, setAlerts] = useState([]);
  const [clearingReports, setClearingReports] = useState(false);
  const [schedulerRunning, setSchedulerRunning] = useState(false);
  const isBusy = Boolean(running || autoRunning || schedulerRunning);

  async function loadReports() {
    try {
      const data = await getDiagnosticReports();
      setReports(data);
      return data;
    } catch {
      setError("Could not load diagnostic reports.");
      return [];
    }
  }

  async function handleAutoRun() {
    try {
    setAutoRunning(true);
    setError("");
    setStatusMessage("");

    const result = await runAutoDiagnostics();

    if (result.reports?.length > 0) {
      setActiveResult(result);
      setActiveType("Auto Diagnosis");
    }

    await loadReports();
    await loadAlerts();
    setStatusMessage(
      `Auto Run scanned ${result.agents_scanned} agents and created ${result.reports_created} reports.`
    );
    } catch (error) {
    setError(getErrorMessage(error, "Could not run autonomous diagnostics."));
    } finally {
    setAutoRunning(false);
    }
  }

  async function loadAlerts() {
    try {
      const data = await getAlerts();
      setAlerts(data);
    } catch {
      setError("Could not load alerts.");
    }
  }

  async function handleSchedulerRun() {
    try {
      setSchedulerRunning(true);
      setError("");
      setStatusMessage("");

      const result = await runScheduler();

      const latestReports = await loadReports();
      if (latestReports[0]) {
        setActiveResult(latestReports[0].payload);
        setActiveType(latestReports[0].report_type);
      }
      await loadAlerts();
      setStatusMessage(
        `Scheduler scanned ${result.agents_scanned} agents, created ${result.reports_created} reports, and generated ${result.alerts_created} alerts.`
      );
    } catch (error) {
      setError(getErrorMessage(error, "Could not run scheduler diagnostics."));
    } finally {
      setSchedulerRunning(false);
    }
  }

  async function handleClearReports() {
    if (reports.length === 0 || clearingReports) return;

    const confirmed = window.confirm(
      "Clear all diagnostic report history? This will not delete agents or executions."
    );

    if (!confirmed) return;

    try {
      setClearingReports(true);
      setError("");
      await clearDiagnosticReports();
      setReports([]);
      setActiveResult(null);
      setActiveType("");
    } catch {
      setError("Could not clear diagnostic report history.");
    } finally {
      setClearingReports(false);
    }
  }

  async function loadAgents() {
    try {
      setLoadingAgents(true);
      setError("");

      const data = await getAgents();
      setAgents(data);

      if (!selectedAgentId && data.length > 0) {
        setSelectedAgentId(data[0].id);
      }
    } catch {
      setError("Could not load agents.");
    } finally {
      setLoadingAgents(false);
    }
  }

  async function runDiagnostic(action) {
    if (!selectedAgentId) {
      setError("Select an agent first.");
      return;
    }

    try {
      setRunning(action.key);
      setError("");
      const result = await action.runner(selectedAgentId);
      setActiveResult(result);
      setActiveType(action.label);
      await loadReports();
      await loadAlerts();
    } catch {
      setError(`Could not run ${action.label} diagnostic.`);
    } finally {
      setRunning("");
    }
  }

  useEffect(() => {
    loadAgents();
    loadReports();
    loadAlerts();
  }, []);

  const selectedAgent = agents.find((agent) => agent.id === selectedAgentId);

  return (
    <div className="diagnostics-page">
      <div className="page-heading">
        <div>
          <h2>Diagnostics</h2>
          <p>Run autonomous diagnostic agents against monitored AI systems.</p>
        </div>

        <div className="heading-actions">
          <button onClick={handleAutoRun} disabled={autoRunning}>
            <Brain size={16} />
            {autoRunning ? "Auto Running..." : "Auto Run"}
          </button>

          <button onClick={handleSchedulerRun} disabled={schedulerRunning}>
            <Workflow size={16} />
            {schedulerRunning ? "Scheduling..." : "Run Scheduler"}
          </button>

          <button onClick={loadAgents}>
            <RefreshCw size={16} /> Refresh
          </button>
        </div>

        {/* <button onClick={loadAgents}>
          <RefreshCw size={16} />
          Refresh
        </button> */}
      </div>

      {error && <div className="panel-message error-text">{error}</div>}
      {statusMessage && <div className="panel-message">{statusMessage}</div>}

      {isBusy && (
        <div className="diagnostic-progress panel-card">
          <div className="diagnostic-loader" />
          <div>
            <strong>
              {autoRunning
                ? "Autonomous diagnostics are running"
                : schedulerRunning
                  ? "Scheduler diagnostics are running"
                  : `${activeType || "Diagnostic agent"} is thinking`}
            </strong>
            <p>
              Local Llama reasoning is running for this diagnostic. The prompt
              and output are capped for speed, but every diagnostic path now
              attempts LLM reasoning.
            </p>
          </div>
        </div>
      )}

      <div className="diagnostics-layout">
        <section className="panel-card diagnostic-control-panel">
          <div className="section-title">
            <SearchCode size={18} />
            <h3>Diagnostic Control</h3>
          </div>

          <label>
            Target Agent
            <select
              value={selectedAgentId}
              disabled={loadingAgents}
              onChange={(event) => {
                setSelectedAgentId(event.target.value);
                setActiveResult(null);
              }}
            >
              {agents.map((agent) => (
                <option value={agent.id} key={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
          </label>

          {selectedAgent && (
            <div className="selected-agent-card">
              <strong>{selectedAgent.name}</strong>
              <p>{selectedAgent.description || "No description provided."}</p>

              <div className="agent-meta">
                <span>Model</span>
                <strong>{selectedAgent.model}</strong>
              </div>

              <div className="agent-meta">
                <span>Status</span>
                <StatusBadge status={selectedAgent.status} />
              </div>
            </div>
          )}

          <div className="diagnostic-actions">
            {diagnosticActions.map((action) => {
              const Icon = action.icon;

              return (
                <button
                  key={action.key}
                  onClick={() => runDiagnostic(action)}
                  disabled={isBusy}
                >
                  <Icon size={16} />
                  {running === action.key ? "Running..." : action.label}
                </button>
              );
            })}
          </div>
        </section>

        <section className="panel-card diagnostic-result-panel">
          <div className="section-title">
            <Brain size={18} />
            <h3>{activeType || "Diagnostic Result"}</h3>
          </div>

          {!activeResult ? (
            <p className="muted-text">
              Run a diagnostic to see agent-generated analysis.
            </p>
          ) : (
            activeResult.reports ? (
              <AutoRunReport
                result={activeResult}
                onSelectReport={(report) => {
                  setActiveResult(report);
                  setActiveType(`Auto Diagnosis - ${report.agent_name}`);
                }}
              />
            ) : (
              <DiagnosticReport result={activeResult} />
            )
          )}
        </section>

        <section className="panel-card report-history-panel">
          <div className="panel-section-header">
            <div className="section-title">
              <Brain size={18} />
              <h3>Diagnostic Report History</h3>
            </div>

            <button
              className="danger-button"
              onClick={handleClearReports}
              disabled={clearingReports || reports.length === 0}
              type="button"
            >
              <Trash2 size={16} />
              {clearingReports ? "Clearing..." : "Clear History"}
            </button>
          </div>

          {reports.length === 0 ? (
            <p className="muted-text">No diagnostic reports saved yet.</p>
          ) : (
            <div className="report-history-list">
              {reports.map((report) => (
                <button
                  key={report.id}
                  className="report-history-item"
                  onClick={() => {
                    setActiveResult(report.payload);
                    setActiveType(report.report_type);
                  }}
                >
                  <div>
                    <strong>{report.agent_name}</strong>
                    <p>{formatIndiaTime(report.created_at)}</p>
                  </div>

                  <span>{report.report_type}</span>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="panel-card alerts-panel">
          <div className="section-title">
            <AlertTriangle size={18} />
            <h3>Autonomous Alerts</h3>
          </div>

          {alerts.length === 0 ? (
            <p className="muted-text">No alerts generated yet.</p>
          ) : (
            <div className="alerts-list">
              {alerts.map((alert) => (
                <div className={`alert-item ${alert.severity}`} key={alert.id}>
                  <div>
                    <strong>{alert.title}</strong>
                    <p>{alert.message}</p>
                    <span>
                      {alert.agent_name} - {alert.source}
                    </span>
                  </div>

                  <em>{alert.severity}</em>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
