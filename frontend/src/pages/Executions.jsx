// export default function Executions() {
//   return <h2>Executions</h2>;
// }

// import { Eye, RefreshCw } from "lucide-react";
// import { useEffect, useState } from "react";
// import StatusBadge from "../components/common/StatusBadge";
// import ExecutionTimeline from "../components/executions/ExecutionTimeline";
// import {
//   getExecutions,
//   getFlightRecorder,
// } from "../services/executionService";

// function formatCost(value) {
//   return `$${Number(value || 0).toFixed(4)}`;
// }

// function formatDate(value) {
//   if (!value) return "Unknown";
//   return new Date(value).toLocaleString();
// }

// export default function Executions() {
//   const [executions, setExecutions] = useState([]);
//   const [selectedExecution, setSelectedExecution] = useState(null);
//   const [flightRecorder, setFlightRecorder] = useState(null);
//   const [loading, setLoading] = useState(true);
//   const [timelineLoading, setTimelineLoading] = useState(false);
//   const [error, setError] = useState("");

//   async function loadExecutions() {
//     try {
//       setLoading(true);
//       setError("");
//       const data = await getExecutions();
//       setExecutions(data);
//     } catch {
//       setError("Could not load executions.");
//     } finally {
//       setLoading(false);
//     }
//   }

//   async function openFlightRecorder(execution) {
//     try {
//       setSelectedExecution(execution);
//       setTimelineLoading(true);
//       const data = await getFlightRecorder(execution.id);
//       setFlightRecorder(data);
//     } catch {
//       setError("Could not load flight recorder.");
//     } finally {
//       setTimelineLoading(false);
//     }
//   }

//   useEffect(() => {
//     loadExecutions();
//   }, []);

//   return (
//     <div className="executions-page">
//       <div className="page-heading">
//         <div>
//           <h2>Executions</h2>
//           <p>Review agent runs, costs, latency, failures, and replay timelines.</p>
//         </div>

//         <button onClick={loadExecutions}>
//           <RefreshCw size={16} />
//           Refresh
//         </button>
//       </div>

//       {error && <div className="panel-message error-text">{error}</div>}

//       <div className="executions-layout">
//         <div className="execution-table panel-card">
//           <div className="table-header">
//             <span>Execution</span>
//             <span>Status</span>
//             <span>Latency</span>
//             <span>Cost</span>
//             <span>Tokens</span>
//             <span>Action</span>
//           </div>

//           {loading ? (
//             <div className="panel-message">Loading executions...</div>
//           ) : executions.length === 0 ? (
//             <div className="panel-message">No executions found.</div>
//           ) : (
//             executions.map((execution) => (
//               <div className="table-row" key={execution.id}>
//                 <div>
//                   <strong>{execution.input}</strong>
//                   <p>{formatDate(execution.created_at)}</p>
//                 </div>

//                 <StatusBadge status={execution.status} />

//                 <span>{execution.latency_ms} ms</span>
//                 <span>{formatCost(execution.cost)}</span>
//                 <span>{execution.total_tokens}</span>

//                 <button
//                   className="ghost-button"
//                   onClick={() => openFlightRecorder(execution)}
//                 >
//                   <Eye size={16} />
//                   Replay
//                 </button>
//               </div>
//             ))
//           )}
//         </div>

//         <aside className="flight-panel panel-card">
//           <div className="section-title">
//             <Eye size={18} />
//             <h3>Flight Recorder</h3>
//           </div>

//           {!selectedExecution ? (
//             <p className="muted-text">Select an execution to replay its timeline.</p>
//           ) : (
//             <>
//               <div className="flight-summary">
//                 <span>Status</span>
//                 <StatusBadge status={selectedExecution.status} />
//               </div>

//               <div className="flight-summary">
//                 <span>Latency</span>
//                 <strong>{selectedExecution.latency_ms} ms</strong>
//               </div>

//               <div className="flight-summary">
//                 <span>Cost</span>
//                 <strong>{formatCost(selectedExecution.cost)}</strong>
//               </div>

//               {timelineLoading ? (
//                 <div className="panel-message">Loading timeline...</div>
//               ) : (
//                 <ExecutionTimeline timeline={flightRecorder?.timeline || []} />
//               )}
//             </>
//           )}
//         </aside>
//       </div>
//     </div>
//   );
// }



import { Eye, Play, Plus, RefreshCw, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import StatusBadge from "../components/common/StatusBadge";
import ExecutionTimeline from "../components/executions/ExecutionTimeline";
import { getAgents } from "../services/agentService";
import {
  createExecution,
  clearExecutions,
  getExecutions,
  getFlightRecorder,
} from "../services/executionService";
import { formatIndiaDateTime } from "../utils/date";

const initialForm = {
  agent_id: "",
  input: "",
  output: "",
  status: "success",
  error_message: "",
  latency_ms: 1200,
  prompt_tokens: 300,
  completion_tokens: 120,
  total_tokens: 420,
  cost: 0.0012,
};

function formatCost(value) {
  return `$${Number(value || 0).toFixed(4)}`;
}

function formatDate(value) {
  return formatIndiaDateTime(value, "Unknown");
}

function buildTraceSteps(form) {
  const baseSteps = [
    {
      step_type: "llm",
      name: "planner",
      content: "Created an execution plan for the incoming request.",
      metadata: {
        status: "completed",
      },
    },
    {
      step_type: "tool",
      name: "retriever",
      content: "Retrieved supporting context for the agent response.",
      metadata: {
        duration_ms: Math.max(120, Math.round(Number(form.latency_ms) * 0.35)),
      },
    },
  ];

  if (form.status === "failed") {
    return [
      ...baseSteps,
      {
        step_type: "error",
        name: "execution_error",
        content: form.error_message || "Execution failed during processing.",
        metadata: {
          recoverable: true,
        },
      },
    ];
  }

  return [
    ...baseSteps,
    {
      step_type: "llm",
      name: "final_response",
      content: "Generated the final output for the user request.",
      metadata: {
        status: "completed",
      },
    },
  ];
}

function buildToolCalls(form) {
  return [
    {
      name: "retriever",
      input: {
        query: form.input,
      },
      output:
        form.status === "failed"
          ? {
              error: form.error_message || "Retriever failed.",
            }
          : {
              result: "Retrieved relevant context.",
            },
      status: form.status === "failed" ? "failed" : "success",
      duration_ms: Math.max(120, Math.round(Number(form.latency_ms) * 0.35)),
    },
  ];
}

export default function Executions() {
  const [agents, setAgents] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [selectedExecution, setSelectedExecution] = useState(null);
  const [flightRecorder, setFlightRecorder] = useState(null);
  const [replayStarted, setReplayStarted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadData() {
    try {
      setLoading(true);
      setError("");

      const [agentData, executionData] = await Promise.all([
        getAgents(),
        getExecutions(),
      ]);

      setAgents(agentData);
      setExecutions(executionData);
      setSelectedExecution((current) => current || executionData[0] || null);

      if (!form.agent_id && agentData.length > 0) {
        setForm((current) => ({
          ...current,
          agent_id: agentData[0].id,
        }));
      }
    } catch {
      setError("Could not load execution data.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateExecution(event) {
    event.preventDefault();

    if (!form.agent_id) {
      setError("Create or select an agent first.");
      return;
    }

    try {
      setSaving(true);
      setError("");

      const promptTokens = Number(form.prompt_tokens);
      const completionTokens = Number(form.completion_tokens);
      const totalTokens =
        Number(form.total_tokens) || promptTokens + completionTokens;

      await createExecution({
        agent_id: form.agent_id,
        input: form.input,
        output: form.status === "failed" ? null : form.output,
        status: form.status,
        error_message: form.status === "failed" ? form.error_message : null,
        latency_ms: Number(form.latency_ms),
        prompt_tokens: promptTokens,
        completion_tokens: completionTokens,
        total_tokens: totalTokens,
        cost: Number(form.cost),
        tool_calls: buildToolCalls(form),
        trace_steps: buildTraceSteps(form),
      });

      setForm((current) => ({
        ...initialForm,
        agent_id: current.agent_id,
      }));

      await loadData();
      setReplayStarted(false);
    } catch {
      setError("Could not create execution.");
    } finally {
      setSaving(false);
    }
  }

  function selectExecution(execution) {
    setSelectedExecution(execution);
    setFlightRecorder(null);
    setReplayStarted(false);
  }

  async function startFlightRecorder() {
    if (!selectedExecution) return;

    try {
      setTimelineLoading(true);
      setReplayStarted(true);
      const data = await getFlightRecorder(selectedExecution.id);
      setFlightRecorder(data);
    } catch {
      setError("Could not load flight recorder.");
    } finally {
      setTimelineLoading(false);
    }
  }

  async function handleClearExecutions() {
    if (executions.length === 0 || clearing) return;

    const confirmed = window.confirm(
      "Clear all logged executions? This will also remove their flight recorder timelines."
    );

    if (!confirmed) return;

    try {
      setClearing(true);
      setError("");
      await clearExecutions();
      setExecutions([]);
      setSelectedExecution(null);
      setFlightRecorder(null);
      setReplayStarted(false);
    } catch {
      setError("Could not clear execution history.");
    } finally {
      setClearing(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="executions-page">
      <div className="page-heading">
        <div>
          <h2>Executions</h2>
          <p>Log agent runs, inspect performance, and replay execution timelines.</p>
        </div>

        <button onClick={loadData}>
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {error && <div className="panel-message error-text">{error}</div>}

      <div className="execution-create-layout">
        <form className="panel-card execution-form" onSubmit={handleCreateExecution}>
          <div className="section-title">
            <Plus size={18} />
            <h3>Log Execution</h3>
          </div>

          <div className="form-grid two">
            <label>
              Agent
              <select
                value={form.agent_id}
                required
                onChange={(event) =>
                  setForm({ ...form, agent_id: event.target.value })
                }
              >
                {agents.map((agent) => (
                  <option value={agent.id} key={agent.id}>
                    {agent.name}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Status
              <select
                value={form.status}
                onChange={(event) =>
                  setForm({ ...form, status: event.target.value })
                }
              >
                <option value="success">success</option>
                <option value="failed">failed</option>
                <option value="running">running</option>
              </select>
            </label>
          </div>

          <label>
            Input
            <textarea
              value={form.input}
              required
              rows={3}
              placeholder="What did the user ask this agent?"
              onChange={(event) => setForm({ ...form, input: event.target.value })}
            />
          </label>

          {form.status !== "failed" ? (
            <label>
              Output
              <textarea
                value={form.output}
                rows={3}
                placeholder="What did the agent return?"
                onChange={(event) =>
                  setForm({ ...form, output: event.target.value })
                }
              />
            </label>
          ) : (
            <label>
              Error Message
              <textarea
                value={form.error_message}
                rows={3}
                placeholder="Execution timed out after 30 seconds"
                onChange={(event) =>
                  setForm({ ...form, error_message: event.target.value })
                }
              />
            </label>
          )}

          <div className="form-grid four">
            <label>
              Latency
              <input
                type="number"
                min="0"
                value={form.latency_ms}
                onChange={(event) =>
                  setForm({ ...form, latency_ms: event.target.value })
                }
              />
            </label>

            <label>
              Prompt Tokens
              <input
                type="number"
                min="0"
                value={form.prompt_tokens}
                onChange={(event) =>
                  setForm({ ...form, prompt_tokens: event.target.value })
                }
              />
            </label>

            <label>
              Completion Tokens
              <input
                type="number"
                min="0"
                value={form.completion_tokens}
                onChange={(event) =>
                  setForm({ ...form, completion_tokens: event.target.value })
                }
              />
            </label>

            <label>
              Cost
              <input
                type="number"
                min="0"
                step="0.0001"
                value={form.cost}
                onChange={(event) =>
                  setForm({ ...form, cost: event.target.value })
                }
              />
            </label>
          </div>

          <button type="submit" disabled={saving}>
            {saving ? "Logging..." : "Log Execution"}
          </button>
        </form>
      </div>

      <div className="executions-layout">
        <div className="execution-table panel-card">
          <div className="panel-table-toolbar">
            <div>
              <strong>Execution History</strong>
              <span>{executions.length} saved runs</span>
            </div>

            <button
              className="danger-button"
              onClick={handleClearExecutions}
              disabled={loading || clearing || executions.length === 0}
              type="button"
            >
              <Trash2 size={16} />
              {clearing ? "Clearing..." : "Clear History"}
            </button>
          </div>

          <div className="table-header">
            <span>Execution</span>
            <span>Status</span>
            <span>Latency</span>
            <span>Cost</span>
            <span>Tokens</span>
            <span>Action</span>
          </div>

          {loading ? (
            <div className="panel-message">Loading executions...</div>
          ) : executions.length === 0 ? (
            <div className="panel-message">No executions found.</div>
          ) : (
            executions.map((execution) => (
              <button
                className={
                  selectedExecution?.id === execution.id
                    ? "table-row execution-row selected"
                    : "table-row execution-row"
                }
                key={execution.id}
                onClick={() => selectExecution(execution)}
                type="button"
              >
                <div>
                  <strong>{execution.input}</strong>
                  <p>{formatDate(execution.created_at)}</p>
                </div>

                <StatusBadge status={execution.status} />

                <span>{execution.latency_ms} ms</span>
                <span>{formatCost(execution.cost)}</span>
                <span>{execution.total_tokens}</span>

                <span className="ghost-button">
                  <Eye size={16} />
                  Select
                </span>
              </button>
            ))
          )}
        </div>

        <aside className="flight-panel panel-card">
          <div className="section-title">
            <Eye size={18} />
            <h3>Flight Recorder</h3>
          </div>

          {!selectedExecution ? (
            <div className="flight-empty-state">
              <Eye size={22} />
              <strong>No execution selected</strong>
              <p className="muted-text">
                Click any execution row on the left, then start the replay.
              </p>
            </div>
          ) : (
            <>
              <div className="selected-execution-summary">
                <span>Selected execution</span>
                <strong>{selectedExecution.input}</strong>
              </div>

              <div className="flight-summary">
                <span>Status</span>
                <StatusBadge status={selectedExecution.status} />
              </div>

              <div className="flight-summary">
                <span>Latency</span>
                <strong>{selectedExecution.latency_ms} ms</strong>
              </div>

              <div className="flight-summary">
                <span>Cost</span>
                <strong>{formatCost(selectedExecution.cost)}</strong>
              </div>

              <button
                className="primary-wide-button"
                onClick={startFlightRecorder}
                disabled={timelineLoading}
              >
                <Play size={16} />
                {timelineLoading ? "Starting Replay..." : "Start Replay"}
              </button>

              {timelineLoading ? (
                <div className="panel-message">Loading timeline...</div>
              ) : replayStarted ? (
                <ExecutionTimeline timeline={flightRecorder?.timeline || []} />
              ) : (
                <p className="muted-text replay-hint">
                  Replay is ready. Press Start Replay to load the timeline.
                </p>
              )}
            </>
          )}
        </aside>
      </div>
    </div>
  );
}
