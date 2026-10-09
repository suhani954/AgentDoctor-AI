import api from "./api";

export async function runMonitoringDiagnostic(agentId) {
  const response = await api.post(`/diagnostics/monitor/${agentId}`);
  return response.data;
}

export async function runRootCauseDiagnostic(agentId) {
  const response = await api.post(`/diagnostics/root-cause/${agentId}`);
  return response.data;
}

export async function runOptimizationDiagnostic(agentId) {
  const response = await api.post(`/diagnostics/optimize/${agentId}`);
  return response.data;
}

export async function runIncidentDiagnostic(agentId) {
  const response = await api.post(`/diagnostics/incident/${agentId}`);
  return response.data;
}

export async function runFullDiagnostic(agentId) {
  const response = await api.post(`/diagnostics/run/${agentId}`);
  return response.data;
}

export async function runAutoDiagnostics() {
  const response = await api.post("/diagnostics/auto-run");
  return response.data;
}

export async function getDiagnosticReports() {
  const response = await api.get("/diagnostics/reports");
  return response.data;
}

export async function clearDiagnosticReports() {
  const response = await api.delete("/diagnostics/reports");
  return response.data;
}

export async function runPromptInjectionDiagnostic(agentId) {
  const response = await api.post(`/diagnostics/prompt-injection/${agentId}`);
  return response.data;
}

export async function runHallucinationDiagnostic(agentId) {
  const response = await api.post(`/diagnostics/hallucination/${agentId}`);
  return response.data;
}

export async function runEvaluationDiagnostic(agentId) {
  const response = await api.post(`/diagnostics/evaluate/${agentId}`);
  return response.data;
}

export async function runWorkflowEvolutionDiagnostic(agentId) {
  const response = await api.post(`/diagnostics/workflow-evolution/${agentId}`);
  return response.data;
}
