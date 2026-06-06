/**
 * Typed API client for the CodeGuard backend.
 * Every method returns a strongly-typed promise; failures throw `ApiError`.
 */

import type {
  AnalysisCapabilities,
  AnalysisReport,
  AnalysisRequest,
  ComparisonRead,
  ComparisonRequest,
  SavedLabCreate,
  SavedLabSummary,
  SubmissionCreate,
  SubmissionRead,
  SubmissionSummary,
} from "../types/api";
import { getWorkspaceId } from "../util/workspace";

const BASE_URL = "/api";

/** Header that scopes submission requests to the caller's browser tab. */
const WORKSPACE_HEADER = "X-Workspace";

export class ApiError extends Error {
  public readonly status: number;

  public constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      [WORKSPACE_HEADER]: getWorkspaceId(),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const detail = await safeDetail(response);
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function safeDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      return body.detail;
    }
    return JSON.stringify(body.detail ?? body);
  } catch {
    return response.statusText;
  }
}

export const api = {
  listSubmissions(): Promise<SubmissionSummary[]> {
    return request<SubmissionSummary[]>("/submissions");
  },

  getSubmission(id: number): Promise<SubmissionRead> {
    return request<SubmissionRead>(`/submissions/${id}`);
  },

  createSubmission(payload: SubmissionCreate): Promise<SubmissionRead> {
    return request<SubmissionRead>("/submissions", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /** Upload a raw `.c` file via multipart/form-data. */
  async uploadSubmission(file: File, name?: string): Promise<SubmissionRead> {
    const form = new FormData();
    form.append("file", file);
    const query = name && name.trim() !== "" ? `?name=${encodeURIComponent(name.trim())}` : "";
    // NB: do not set Content-Type; the browser adds the multipart boundary.
    const response = await fetch(`${BASE_URL}/submissions/upload${query}`, {
      method: "POST",
      headers: { [WORKSPACE_HEADER]: getWorkspaceId() },
      body: form,
    });
    if (!response.ok) {
      throw new ApiError(response.status, await safeDetail(response));
    }
    return (await response.json()) as SubmissionRead;
  },

  deleteSubmission(id: number): Promise<void> {
    return request<void>(`/submissions/${id}`, { method: "DELETE" });
  },

  compare(payload: ComparisonRequest): Promise<ComparisonRead> {
    return request<ComparisonRead>("/comparisons", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  analysisCapabilities(): Promise<AnalysisCapabilities> {
    return request<AnalysisCapabilities>("/analysis/capabilities");
  },

  analyze(payload: AnalysisRequest): Promise<AnalysisReport> {
    return request<AnalysisReport>("/analysis", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /** Save an analysis report behind a unique name + password. */
  saveLab(payload: SavedLabCreate): Promise<SavedLabSummary> {
    return request<SavedLabSummary>("/labs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /** Reopen a saved score set by its name + password (no browsable list). */
  unlockLab(name: string, password: string): Promise<AnalysisReport> {
    return request<AnalysisReport>("/labs/unlock", {
      method: "POST",
      body: JSON.stringify({ name, password }),
    });
  },
} as const;
