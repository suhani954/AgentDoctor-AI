import {
  Activity,
  BarChart3,
  Bot,
  HelpCircle,
  LogOut,
  Radio,
  SearchCode,
} from "lucide-react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

const navItems = [
  { label: "Dashboard", path: "/dashboard", icon: BarChart3 },
  { label: "Agents", path: "/agents", icon: Bot },
  { label: "Executions", path: "/executions", icon: Activity },
  { label: "Diagnostics", path: "/diagnostics", icon: SearchCode },
  { label: "Guide", path: "/guide", icon: HelpCircle },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">AD</div>
          <div>
            <h1>AgentDoctor AI</h1>
            <p>Operations Command</p>
          </div>
        </div>

        <div className="system-chip">System Online</div>

        <p className="nav-section-label">Operations</p>

        <nav className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = location.pathname.startsWith(item.path);

            return (
              <Link
                key={item.path}
                to={item.path}
                className={active ? "nav-item active" : "nav-item"}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-account">
          <div>
            <p>Operator</p>
            <strong>{user?.email}</strong>
          </div>

          <button className="logout-button" onClick={handleLogout} title="Logout">
            <LogOut size={18} />
          </button>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div className="topbar-left">
            <span className="topbar-status env">Development</span>
            <span className="topbar-status">
              <Radio size={14} />
              Live telemetry
            </span>
          </div>

          <div className="topbar-account">
            <p>Signed in as</p>
            <strong>{user?.email}</strong>
          </div>
        </header>

        <section className="page-content">
          <Outlet />
        </section>
      </main>
    </div>
  );
}
