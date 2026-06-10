const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
const API_BASE_URL = (configuredApiBaseUrl || "http://localhost:8000/api").replace(/\/+$/, "");

export type DocumentChunk = {
  id: number;
  document: number;
  chunk_text: string;
  embedding: unknown[];
  created_at: string;
};

export type DocumentRecord = {
  id: number;
  title: string;
  source_type: string;
  content: string;
  original_filename: string;
  file_type: string;
  file_size: number | null;
  ingestion_status: "completed";
  ingestion_error: string;
  created_at: string;
  updated_at: string;
  chunks: DocumentChunk[];
};

export type AgentStep = {
  id: number;
  research_run: number;
  step_type: "plan" | "retrieve" | "tool_call" | "reflect" | "final";
  input_data: AgentStepData;
  output_data: AgentStepData;
  created_at: string;
};

export type RetrievalEvidence = {
  citation_id: number;
  chunk_id: number;
  document_id: number;
  document_title: string;
  chunk_text: string;
  score: number;
  retrieval_mode: "embedding" | "keyword";
  ai_mode?: "mock" | "openai";
};

export type CitationSource = {
  citation_id: number;
  document_title: string;
  chunk_id: number;
  score: number;
  excerpt: string;
};

export type AgentStepData = Record<string, unknown> & {
  ai_mode?: "mock" | "openai";
  chunks?: RetrievalEvidence[];
  evidence?: RetrievalEvidence[];
  sources_used?: CitationSource[];
  final_answer?: string;
};

export type ResearchRun = {
  id: number;
  user_query: string;
  status: "pending" | "running" | "completed" | "failed";
  final_answer: string;
  confidence_score: number | null;
  created_at: string;
  updated_at: string;
  steps: AgentStep[];
};

type CreateDocumentInput = {
  title: string;
  source_type: string;
  content: string;
};

export type ClearResponse = {
  deleted: number;
  deleted_rows: number;
  details: Record<string, number>;
};

async function request<T = void>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers);
  if (typeof options?.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const body = await parseErrorResponse(response);
    if (response.status === 429) {
      const retryMessage =
        typeof body.retry_after === "number"
          ? ` Try again in about ${Math.ceil(body.retry_after)} seconds.`
          : " Please wait before trying again.";
      throw new Error(`Too many requests.${retryMessage}`);
    }
    throw new Error(getErrorMessage(body, response.status));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

function getErrorMessage(body: Record<string, unknown>, status: number): string {
  if (typeof body.detail === "string") return body.detail;

  for (const [field, value] of Object.entries(body)) {
    const message = Array.isArray(value) ? value[0] : value;
    if (typeof message === "string") {
      const label = field.replace(/_/g, " ");
      return `${label.charAt(0).toUpperCase()}${label.slice(1)}: ${message}`;
    }
  }

  return `Request failed with status ${status}`;
}

async function parseErrorResponse(response: Response): Promise<Record<string, unknown>> {
  try {
    return (await response.json()) as Record<string, unknown>;
  } catch {
    return {};
  }
}

export const api = {
  getDocuments: () => request<DocumentRecord[]>("/documents/"),
  createDocument: (input: CreateDocumentInput) =>
    request<DocumentRecord>("/documents/", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  uploadDocument: (file: File, title: string) => {
    const formData = new FormData();
    formData.append("file", file);
    if (title.trim()) formData.append("title", title.trim());
    return request<DocumentRecord>("/documents/upload/", {
      method: "POST",
      body: formData,
    });
  },
  deleteDocument: (id: number) =>
    request(`/documents/${id}/`, {
      method: "DELETE",
    }),
  clearDocuments: () =>
    request<ClearResponse>("/documents/clear/", {
      method: "DELETE",
    }),
  getResearchRuns: () => request<ResearchRun[]>("/research-runs/"),
  createResearchRun: (userQuery: string) =>
    request<ResearchRun>("/research-runs/", {
      method: "POST",
      body: JSON.stringify({ user_query: userQuery }),
    }),
  deleteResearchRun: (id: number) =>
    request(`/research-runs/${id}/`, {
      method: "DELETE",
    }),
  clearResearchRuns: () =>
    request<ClearResponse>("/research-runs/clear/", {
      method: "DELETE",
    }),
  getResearchRunSteps: (id: number) => request<AgentStep[]>(`/research-runs/${id}/steps/`),
};
