import type {
  AuthCredentials,
  ExecutionJobRead,
  IntegrationStatus,
  GoalCreateRequest,
  GoalCreateResponse,
  Goal,
  PlanFinalizeRequest,
  PlanFinalizeResponse,
  PlanFinalizeJobCreateResponse,
  PlanFinalizeJobRead,
  Plan,
  RagQueryRequest,
  RagQueryResponse,
  RagIngestResponse,
  RegisterPayload,
  TokenResponse,
  WorkspaceCreateRequest,
  Workspace,
} from "@/lib/types";
import { getStoredAuthToken } from "@/lib/auth";

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

function getBaseUrl(): string {
  return process.env.NEXT_PUBLIC_BACKEND_API_URL ?? "http://127.0.0.1:8000";
}

function buildUrl(path: string): string {
  return new URL(path, getBaseUrl()).toString();
}

async function parseErrorResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function formatErrorDetail(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object") {
          return JSON.stringify(item);
        }
        return String(item);
      })
      .join(", ");
  }
  if (detail && typeof detail === "object") {
    try {
      return JSON.stringify(detail);
    } catch {
      return "Request failed";
    }
  }
  if (detail === null || detail === undefined) {
    return "Request failed";
  }
  return String(detail);
}

export class BackendApiClient {
  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const headers = new Headers(options.headers);
    const token = getStoredAuthToken();

    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    let body: BodyInit | undefined;
    if (options.body instanceof FormData) {
      body = options.body;
    } else if (options.body !== undefined) {
      headers.set("Content-Type", "application/json");
      body = JSON.stringify(options.body);
    }

    const response = await fetch(buildUrl(path), {
      ...options,
      headers,
      body,
    });

    if (!response.ok) {
      const payload = await parseErrorResponse(response);
      const message =
        typeof payload === "object" && payload !== null && "detail" in payload
          ? formatErrorDetail((payload as { detail?: unknown }).detail)
          : `Request failed with status ${response.status}`;
      throw new ApiError(message, response.status, payload);
    }

    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      return (await response.json()) as T;
    }

    return undefined as T;
  }

  register(payload: RegisterPayload): Promise<TokenResponse> {
    return this.request<TokenResponse>("/auth/register", {
      method: "POST",
      body: payload,
    });
  }

  login(payload: AuthCredentials): Promise<TokenResponse> {
    return this.request<TokenResponse>("/auth/login", {
      method: "POST",
      body: payload,
    });
  }

  createWorkspace(payload: WorkspaceCreateRequest): Promise<Workspace> {
    return this.request<Workspace>("/workspaces", {
      method: "POST",
      body: payload,
    });
  }

  listWorkspaces(userId: string): Promise<Workspace[]> {
    return this.request<Workspace[]>(`/workspaces?user_id=${encodeURIComponent(userId)}`, {
      method: "GET",
    });
  }

  createGoal(payload: GoalCreateRequest): Promise<GoalCreateResponse> {
    return this.request<GoalCreateResponse>("/goals", {
      method: "POST",
      body: payload,
    });
  }

  getGoal(goalId: string): Promise<Goal> {
    return this.request<Goal>(`/goals/${goalId}`, {
      method: "GET",
    });
  }

  finalizePlan(payload: PlanFinalizeRequest): Promise<PlanFinalizeResponse> {
    return this.request<PlanFinalizeResponse>("/plans/finalize", {
      method: "POST",
      body: payload,
    });
  }

  finalizePlanAsync(payload: PlanFinalizeRequest): Promise<PlanFinalizeJobCreateResponse> {
    return this.request<PlanFinalizeJobCreateResponse>("/plans/finalize/async", {
      method: "POST",
      body: payload,
    });
  }

  createExecutionJobsForPlan(planId: string): Promise<Plan> {
    return this.request<Plan>(`/plans/${planId}/execution-jobs`, {
      method: "POST",
    });
  }

  getPlanFinalizeJob(jobId: string): Promise<PlanFinalizeJobRead> {
    return this.request<PlanFinalizeJobRead>(`/plans/jobs/${jobId}`, {
      method: "GET",
    });
  }

  getExecutionJob(jobId: string): Promise<ExecutionJobRead> {
    return this.request<ExecutionJobRead>(`/ai/execution/jobs/${jobId}`, {
      method: "GET",
    });
  }

  listExecutionJobs(status?: string): Promise<ExecutionJobRead[]> {
    const query = status ? `?job_status=${encodeURIComponent(status)}` : "";
    return this.request<ExecutionJobRead[]>(`/ai/execution/jobs${query}`, {
      method: "GET",
    });
  }

  approveExecutionJob(jobId: string): Promise<ExecutionJobRead> {
    return this.request<ExecutionJobRead>(`/ai/execution/jobs/${jobId}/approve`, {
      method: "POST",
    });
  }

  rejectExecutionJob(jobId: string, reason?: string): Promise<ExecutionJobRead> {
    return this.request<ExecutionJobRead>(`/ai/execution/jobs/${jobId}/reject`, {
      method: "POST",
      body: reason ? { reason } : {},
    });
  }

  listIntegrations(): Promise<IntegrationStatus[]> {
    return this.request<IntegrationStatus[]>("/ai/integrations", {
      method: "GET",
    });
  }

  queryKnowledge(payload: RagQueryRequest): Promise<RagQueryResponse> {
    return this.request<RagQueryResponse>("/ai/rag/query", {
      method: "POST",
      body: payload,
    });
  }

  ingestDocument(payload: {
    file?: File | null;
    text?: string | null;
    userId?: string | null;
    documentId?: string | null;
    source?: string;
    filename?: string;
  }): Promise<RagIngestResponse> {
    const formData = new FormData();

    if (payload.file) {
      formData.append("file", payload.file, payload.filename ?? payload.file.name);
    }
    if (payload.text) {
      formData.append("text", payload.text);
    }
    if (payload.userId) {
      formData.append("user_id", payload.userId);
    }
    if (payload.documentId) {
      formData.append("document_id", payload.documentId);
    }
    if (payload.source) {
      formData.append("source", payload.source);
    }
    if (payload.filename) {
      formData.append("filename", payload.filename);
    }

    return this.request<RagIngestResponse>("/ai/rag/ingest", {
      method: "POST",
      body: formData,
    });
  }
}

export const backendApi = new BackendApiClient();
