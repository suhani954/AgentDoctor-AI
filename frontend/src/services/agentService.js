import api from "./api";

export async function getAgents() {
  const response = await api.get("/agents");
  return response.data;
}

export async function createAgent(payload) {
  const response = await api.post("/agents", payload);
  return response.data;
}

export async function updateAgent(agentId, payload) {
  const response = await api.put(`/agents/${agentId}`, payload);
  return response.data;
}

export async function deleteAgent(agentId) {
  const response = await api.delete(`/agents/${agentId}`);
  return response.data;
}



export async function getAgent(agentId) {
  const response = await api.get(`/agents/${agentId}`);
  return response.data;
}