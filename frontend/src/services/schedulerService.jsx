import api from "./api";

export async function runScheduler() {
  const response = await api.post("/scheduler/run");
  return response.data;
}