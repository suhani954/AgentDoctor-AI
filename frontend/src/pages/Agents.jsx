// export default function Agents() {
//   return <h2>Agents</h2>;
// }

import { Bot, Plus, RefreshCw, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import StatusBadge from "../components/common/StatusBadge";
import { createAgent, deleteAgent, getAgents } from "../services/agentService";
import { Link } from "react-router-dom";

const initialForm = {
  name: "",
  description: "",
  model: "llama3.1:8b",
  status: "active",
};

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function loadAgents() {
    try {
      setLoading(true);
      setError("");
      const data = await getAgents();
      setAgents(data);
    } catch {
      setError("Could not load agents.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(event) {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      await createAgent({
        ...form,
        description: form.description || null,
      });
      setForm(initialForm);
      await loadAgents();
    } catch {
      setError("Could not create agent.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(agentId) {
    const confirmed = window.confirm("Delete this agent?");
    if (!confirmed) return;

    try {
      await deleteAgent(agentId);
      await loadAgents();
    } catch {
      setError("Could not delete agent.");
    }
  }

  useEffect(() => {
    loadAgents();
  }, []);

  return (
    <div className="agents-page">
      <div className="page-heading">
        <div>
          <h2>Agents</h2>
          <p>Register and manage the AI agents monitored by AgentDoctor AI.</p>
        </div>

        <button onClick={loadAgents}>
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {error && <div className="panel-message error-text">{error}</div>}

      <div className="agents-layout">
        <form className="agent-form panel-card" onSubmit={handleCreate}>
          <div className="section-title">
            <Plus size={18} />
            <h3>Create Agent</h3>
          </div>

          <label>
            Agent Name
            <input
              value={form.name}
              placeholder="Research Agent"
              required
              onChange={(event) =>
                setForm({ ...form, name: event.target.value })
              }
            />
          </label>

          <label>
            Description
            <textarea
              value={form.description}
              placeholder="What does this agent do?"
              rows={4}
              onChange={(event) =>
                setForm({ ...form, description: event.target.value })
              }
            />
          </label>

          <label>
            Model
            <select
              value={form.model}
              onChange={(event) =>
                setForm({ ...form, model: event.target.value })
              }
            >
              <option value="llama3.1:8b">llama3.1:8b</option>
              <option value="llama3.2:3b">llama3.2:3b</option>
              <option value="gpt-4o-mini">gpt-4o-mini</option>
              <option value="gpt-4o">gpt-4o</option>
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
              <option value="active">active</option>
              <option value="inactive">inactive</option>
              <option value="error">error</option>
            </select>
          </label>

          <button type="submit" disabled={saving}>
            {saving ? "Creating..." : "Create Agent"}
          </button>
        </form>

        <div className="agents-list">
          {loading ? (
            <div className="panel-message">Loading agents...</div>
          ) : agents.length === 0 ? (
            <div className="panel-message">No agents created yet.</div>
          ) : (
            agents.map((agent) => (
              <div className="agent-card" key={agent.id}>
                <div className="agent-card-header">
                  <div className="agent-icon">
                    <Bot size={20} />
                  </div>

                  <div>
                    <h3>{agent.name}</h3>
                    <p>{agent.description || "No description provided."}</p>
                  </div>
                </div>

                <div className="agent-meta">
                  <span>Model</span>
                  <strong>{agent.model}</strong>
                </div>

                <div className="agent-meta">
                  <span>Status</span>
                  <StatusBadge status={agent.status} />
                </div>

                <div className="agent-actions">
                    <Link className="ghost-button" to={`/agents/${agent.id}`}>
                    View Details
                    </Link>
                    
                  <button
                    className="danger-button"
                    onClick={() => handleDelete(agent.id)}
                  >
                    <Trash2 size={16} />
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}