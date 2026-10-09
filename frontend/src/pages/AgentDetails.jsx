import { Activity, Brain, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import StatusBadge from "../components/common/StatusBadge";
import { getAgentHealthScore } from "../services/analyticsService";
import { getAgent } from "../services/agentService";
import { runFullDiagnostic } from "../services/diagnosticService";
import { getAgentExecutions } from "../services/executionService";
import { formatIndiaDateTime } from "../utils/date";

function formatCost(value) {
  return `$${Number(value || 0).toFixed(4)}`;
}

function formatDate(value) {
  return formatIndiaDateTime(value, "Unknown");
}

export default function AgentDetails() {
  const { agentId } = useParams();

  const [agent, setAgent] = useState(null);
  const [health, setHealth] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [diagnostic, setDiagnostic] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  async function loadAgentDetails() {
    try {
      setLoading(true);
      setError("");

      const [agentData, healthData, executionData] = await Promise.all([
        getAgent(agentId),
        getAgentHealthScore(agentId),
        getAgentExecutions(agentId),
      ]);

      setAgent(agentData);
      setHealth(healthData);
      setExecutions(executionData.slice(0, 8));
    } catch {
      setError("Could not load agent details.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRunDiagnosis() {
    try {
      setRunning(true);
      setError("");

      const result = await runFullDiagnostic(agentId);
      setDiagnostic(result);
    } catch {
      setError("Could not run full diagnosis.");
    } finally {
      setRunning(false);
    }
  }

  useEffect(() => {
    loadAgentDetails();
  }, [agentId]);

  if (loading) {
    return <div className="panel-message">Loading agent details...</div>;
  }

  if (error && !agent) {
    return <div className="panel-message error-text">{error}</div>;
  }

  return (
    <div className="agent-details-page">
      <div className="page-heading">
        <div>
          <h2>{agent.name}</h2>
          <p>{agent.description || "No description provided."}</p>
        </div>

        <button onClick={loadAgentDetails}>
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {error && <div className="panel-message error-text">{error}</div>}

      <div className="agent-detail-grid">
        <section className="panel-card agent-profile-panel">
          <div className="section-title">
            <Activity size={18} />
            <h3>Agent Profile</h3>
          </div>

          <div className="agent-meta">
            <span>Status</span>
            <StatusBadge status={agent.status} />
          </div>

          <div className="agent-meta">
            <span>Model</span>
            <strong>{agent.model}</strong>
          </div>

          <div className="agent-meta">
            <span>Agent ID</span>
            <strong className="mono-text">{agent.id}</strong>
          </div>

          <button className="primary-wide-button" onClick={handleRunDiagnosis}>
            <Brain size={16} />
            {running ? "Running Diagnosis..." : "Run Full Diagnosis"}
          </button>
        </section>

        <section className="panel-card health-panel">
          <div className="health-score-ring">
            <strong>{health.score}</strong>
            <span>/100</span>
          </div>

          <div>
            <h3>{health.grade}</h3>
            <p>Agent Health Score</p>
          </div>
        </section>
      </div>

      <div className="agent-detail-grid wide">
        <section className="panel-card score-breakdown">
          <h3>Score Breakdown</h3>

          <div className="score-row">
            <span>Reliability</span>
            <strong>{health.reliability_score}%</strong>
          </div>

          <div className="score-row">
            <span>Latency</span>
            <strong>{health.latency_score}%</strong>
          </div>

          <div className="score-row">
            <span>Cost Efficiency</span>
            <strong>{health.cost_efficiency_score}%</strong>
          </div>

          <div className="score-row">
            <span>Failure Rate</span>
            <strong>{health.failure_rate}%</strong>
          </div>

          <div className="score-row">
            <span>Average Latency</span>
            <strong>{health.average_latency_ms} ms</strong>
          </div>

          <div className="score-row">
            <span>Average Cost</span>
            <strong>{formatCost(health.average_cost)}</strong>
          </div>
        </section>

        <section className="panel-card score-reasons">
          <h3>Health Reasons</h3>

          {health.reasons.map((reason) => (
            <p key={reason}>{reason}</p>
          ))}
        </section>
      </div>

      {diagnostic && (
        <section className="panel-card diagnosis-summary-panel">
          <div className="section-title">
            <Brain size={18} />
            <h3>Latest Full Diagnosis</h3>
          </div>

          <div className="summary-box">
            <strong>Summary</strong>
            <p>{diagnostic.final_summary}</p>
          </div>

          <div className="executed-agents">
            {diagnostic.executed_agents.map((agentName) => (
              <span key={agentName}>{agentName}</span>
            ))}
          </div>
        </section>
      )}

      <section className="panel-card recent-executions-panel">
        <h3>Recent Executions</h3>

        {executions.length === 0 ? (
          <p className="muted-text">No executions found.</p>
        ) : (
          <div className="compact-table">
            {executions.map((execution) => (
              <div className="compact-row" key={execution.id}>
                <div>
                  <strong>{execution.input}</strong>
                  <p>{formatDate(execution.created_at)}</p>
                </div>

                <StatusBadge status={execution.status} />
                <span>{execution.latency_ms} ms</span>
                <span>{formatCost(execution.cost)}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
