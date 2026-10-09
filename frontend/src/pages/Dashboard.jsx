// export default function Dashboard() {
//   return <h2>Dashboard</h2>;
// }

import { useEffect, useState } from "react";
import { Activity, AlertTriangle, Gauge, Radio, RefreshCw, Wallet } from "lucide-react";
import DashboardChart from "../components/dashboard/DashboardChart";
import MetricCard from "../components/dashboard/MetricCard";
import {
  getCostAnalytics,
  getFailureAnalytics,
  getLatencyAnalytics,
  getOverviewAnalytics,
} from "../services/analyticsService";

function formatCost(value) {
  return `$${Number(value || 0).toFixed(4)}`;
}

function formatPercent(value) {
  return `${Number(value || 0).toFixed(1)}%`;
}

function formatLatency(value) {
  return `${Math.round(value || 0)} ms`;
}

export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [cost, setCost] = useState(null);
  const [latency, setLatency] = useState(null);
  const [failures, setFailures] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      const [overviewData, costData, latencyData, failureData] =
        await Promise.all([
          getOverviewAnalytics(),
          getCostAnalytics(),
          getLatencyAnalytics(),
          getFailureAnalytics(),
        ]);

      setOverview(overviewData);
      setCost(costData);
      setLatency(latencyData);
      setFailures(failureData);
    } catch {
      setError("Could not load dashboard analytics.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  if (loading) {
    return <div className="panel-message">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="panel-message error-text">{error}</div>;
  }

  return (
    <div className="dashboard-page">
      <div className="command-hero">
        <div className="command-hero-copy">
          <span className="eyebrow">Agent Operations Command</span>
          <h2>System intelligence at a glance.</h2>
          <p>
            Monitor agent reliability, cost behavior, execution health, and active
            diagnostic signals from one operational surface.
          </p>
        </div>

        <div className="command-hero-status">
          <span>Health Pulse</span>
          <strong>{formatPercent(overview.success_rate)}</strong>
          <p>Current success rate across monitored executions</p>
          <button onClick={loadDashboard}>
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </div>

      <div className="metrics-grid">
        <MetricCard label="Total Agents" value={overview.total_agents} helper="Registered systems" />
        <MetricCard label="Executions" value={overview.total_executions} helper="Telemetry events" tone="gold" />
        <MetricCard
          label="Success Rate"
          value={formatPercent(overview.success_rate)}
          helper="Reliability signal"
        />
        <MetricCard
          label="Failure Rate"
          value={formatPercent(overview.failure_rate)}
          helper="Incident pressure"
          tone="danger"
        />
        <MetricCard label="Total Cost" value={formatCost(overview.total_cost)} helper="Tracked spend" tone="gold" />
        <MetricCard
          label="Avg Latency"
          value={formatLatency(overview.average_latency_ms)}
          helper="Response time"
          tone="neutral"
        />
      </div>

      <div className="dashboard-command-grid">
        <div className="dashboard-chart-stack">
          <DashboardChart
            title="Cost by Agent"
            data={cost?.cost_by_agent || []}
            dataKey="total_cost"
            color="#0f8f6b"
          />

          <DashboardChart
            title="Latency by Agent"
            data={latency?.latency_by_agent || []}
            dataKey="average_latency_ms"
            color="#b99452"
          />

          <DashboardChart
            title="Failures by Agent"
            data={failures?.failures_by_agent || []}
            dataKey="failed_executions"
            color="#bf3f34"
          />
        </div>

        <aside className="signal-panel">
          <div className="section-title">
            <Radio size={18} />
            <h3>Active Signals</h3>
          </div>

          <div className="signal-card">
            <AlertTriangle size={18} />
            <div>
              <span>Failure pressure</span>
              <strong>{formatPercent(overview.failure_rate)}</strong>
              <p>{failures?.total_failures || 0} failed executions detected</p>
            </div>
          </div>

          <div className="signal-card">
            <Gauge size={18} />
            <div>
              <span>Latency load</span>
              <strong>{formatLatency(overview.average_latency_ms)}</strong>
              <p>Average runtime across executions</p>
            </div>
          </div>

          <div className="signal-card">
            <Wallet size={18} />
            <div>
              <span>Cost footprint</span>
              <strong>{formatCost(overview.total_cost)}</strong>
              <p>{cost?.total_tokens || 0} tokens tracked</p>
            </div>
          </div>

          <div className="signal-card calm">
            <Activity size={18} />
            <div>
              <span>Diagnostic readiness</span>
              <strong>Ready</strong>
              <p>Monitoring, root cause, optimization, and incident agents available</p>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
