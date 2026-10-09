import api from "./api";

export async function getAlerts() {
  const response = await api.get("/alerts");
  return response.data;
}