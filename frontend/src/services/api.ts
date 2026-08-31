import axios from "axios";

// In dev, defaults to "/api", which the Vite dev server proxies to the FastAPI
// backend (see vite.config.ts). Override with VITE_API_BASE_URL to point at the
// backend directly — include the /api suffix, e.g. http://localhost:8000/api
const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const api = axios.create({ baseURL, timeout: 15000 });

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  env: string;
  timestamp: string;
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}
