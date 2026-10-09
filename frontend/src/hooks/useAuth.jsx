import { createContext, useContext, useEffect, useState } from "react";
import { getCurrentUser, loginUser, signupUser } from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  async function loadUser() {
    const token = localStorage.getItem("agentdoctor_token");

    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch {
      localStorage.removeItem("agentdoctor_token");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  async function login(payload) {
    const data = await loginUser(payload);
    localStorage.setItem("agentdoctor_token", data.access_token);
    setUser(data.user);
    return data.user;
  }

  async function signup(payload) {
    const data = await signupUser(payload);
    localStorage.setItem("agentdoctor_token", data.access_token);
    setUser(data.user);
    return data.user;
  }

  function logout() {
    localStorage.removeItem("agentdoctor_token");
    setUser(null);
  }

  useEffect(() => {
    loadUser();
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}