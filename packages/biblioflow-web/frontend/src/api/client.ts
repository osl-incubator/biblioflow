import type { ApiEnvelope, HealthResponse, Project } from "./types";

const API_BASE_URL = import.meta.env.VITE_BIBLIOFLOW_WEB_API_BASE_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(
      payload?.error?.message ?? `Request failed: ${response.status}`,
    );
  }
  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export async function listProjects(): Promise<ApiEnvelope<Project[]>> {
  return request<ApiEnvelope<Project[]>>("/projects");
}

export async function createProject(
  name: string,
): Promise<ApiEnvelope<Project>> {
  return request<ApiEnvelope<Project>>("/projects", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}
