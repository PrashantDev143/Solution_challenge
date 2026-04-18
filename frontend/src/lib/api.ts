import {
  ExplainResponse,
  ScanResponse,
  SimulateSchemaResponse,
  SimulateRequest,
  SimulateResponse,
  UploadResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload && "detail" in payload
        ? String((payload as { detail: string }).detail)
        : "Request failed.";
    throw new Error(detail);
  }

  return payload as T;
}

export async function checkHealth(): Promise<{ status: string; app: string }> {
  return request("/health");
}

export async function uploadCsv(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return request<UploadResponse>("/upload", {
    method: "POST",
    body: formData,
  });
}

export async function scanBias(payload: {
  dataset_path?: string;
  target_column?: string;
}): Promise<ScanResponse> {
  return request<ScanResponse>("/scan", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function simulate(payload: SimulateRequest): Promise<SimulateResponse> {
  return request<SimulateResponse>("/simulate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function getSimulateSchema(payload?: {
  dataset_path?: string;
  target_column?: string;
}): Promise<SimulateSchemaResponse> {
  const params = new URLSearchParams();
  if (payload?.dataset_path) {
    params.set("dataset_path", payload.dataset_path);
  }
  if (payload?.target_column) {
    params.set("target_column", payload.target_column);
  }

  const query = params.toString();
  const path = query ? `/simulate/schema?${query}` : "/simulate/schema";
  return request<SimulateSchemaResponse>(path);
}

export async function explain(payload: {
  group: string;
  count?: number;
  approval_rate: number;
  baseline_rate: number;
  difference: number;
  severity: string;
  ranking_reason?: string;
}): Promise<ExplainResponse> {
  return request<ExplainResponse>("/explain", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function getReport(): Promise<ScanResponse> {
  return request<ScanResponse>("/report");
}
