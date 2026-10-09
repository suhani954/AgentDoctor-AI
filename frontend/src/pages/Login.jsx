import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "demo@agentdoctor.ai",
    password: "AgentDoctorDemo@2026#LocalOnly",
  });
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    try {
      await login(form);
      navigate("/dashboard");
    } catch {
      setError("Invalid email or password.");
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>AgentDoctor AI</h1>
        <p>Sign in to monitor and diagnose your AI agents.</p>

        {error && <div className="error-box">{error}</div>}

        <label>
          Email
          <input
            value={form.email}
            onChange={(event) =>
              setForm({ ...form, email: event.target.value })
            }
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={form.password}
            onChange={(event) =>
              setForm({ ...form, password: event.target.value })
            }
          />
        </label>

        <button type="submit">Login</button>

        <span>
          New here? <Link to="/signup">Create account</Link>
        </span>
      </form>
    </div>
  );
}