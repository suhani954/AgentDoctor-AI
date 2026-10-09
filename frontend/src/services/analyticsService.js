import api from "./api";

export async function getOverviewAnalytics() {
  const response = await api.get("/analytics/overview");
  return response.data;
}

export async function getCostAnalytics() {
  const response = await api.get("/analytics/cost");
  return response.data;
}

export async function getLatencyAnalytics() {
  const response = await api.get("/analytics/latency");
  return response.data;
}

export async function getFailureAnalytics() {
  const response = await api.get("/analytics/failures");
  return response.data;
}



export async function getAgentHealthScore(agentId) {
  const response = await api.get(`/analytics/agents/${agentId}/health`);
  return response.data;
}