const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

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
  created_at: string;
  updated_at: string;
  chunks: DocumentChunk[];
};

export type AgentStep = {
  id: number;
  research_run: number;
  step_type: "plan" | "retrieve" | "tool_call" | "reflect" | "final";
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  created_at: string;
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

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  getDocuments: () => request<DocumentRecord[]>("/documents/"),
  createDocument: (input: CreateDocumentInput) =>
    request<DocumentRecord>("/documents/", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  getResearchRuns: () => request<ResearchRun[]>("/research-runs/"),
  createResearchRun: (userQuery: string) =>
    request<ResearchRun>("/research-runs/", {
      method: "POST",
      body: JSON.stringify({ user_query: userQuery }),
    }),
  getResearchRunSteps: (id: number) => request<AgentStep[]>(`/research-runs/${id}/steps/`),
};
