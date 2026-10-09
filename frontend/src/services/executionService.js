import api from "./api";

export async function getExecutions() {
  const response = await api.get("/executions");
  return response.data;
}

export async function getExecution(executionId) {
  const response = await api.get(`/executions/${executionId}`);
  return response.data;
}

export async function getFlightRecorder(executionId) {
  const response = await api.get(`/executions/${executionId}/flight-recorder`);
  return response.data;
}

export async function createExecution(payload) {
  const response = await api.post("/executions", payload);
  return response.data;
}

export async function clearExecutions() {
  const response = await api.delete("/executions");
  return response.data;
}

export async function getAgentExecutions(agentId) {
  const response = await api.get(`/agents/${agentId}/executions`);
  return response.data;
}
