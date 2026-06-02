import { FormEvent, MouseEvent, useEffect, useMemo, useState } from "react";

import { AgentStep, ResearchRun, RetrievalEvidence, api } from "../api/client";

const stepLabels: Record<AgentStep["step_type"], string> = {
  plan: "Plan",
  retrieve: "Retrieval",
  tool_call: "Tool call",
  reflect: "Reflection",
  final: "Final",
};

export function ResearchDashboard() {
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;

    api
      .getResearchRuns()
      .then((data) => {
        if (!ignore) {
          setRuns(data);
          setSelectedRunId(data[0]?.id ?? null);
        }
      })
      .catch((err: Error) => {
        if (!ignore) setError(err.message);
      })
      .finally(() => {
        if (!ignore) setIsLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, []);

  const selectedRun = useMemo(
    () => runs.find((run) => run.id === selectedRunId) ?? runs[0],
    [runs, selectedRunId],
  );
  const selectedEvidence = useMemo(() => getEvidence(selectedRun), [selectedRun]);
  const selectedAiMode = useMemo(() => getAiMode(selectedRun), [selectedRun]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!query.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const run = await api.createResearchRun(query.trim());
      setRuns((current) => [run, ...current]);
      setSelectedRunId(run.id);
      setQuery("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create research run");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDeleteRun(event: MouseEvent<HTMLButtonElement>, run: ResearchRun) {
    event.stopPropagation();
    if (!window.confirm(`Delete research run "${run.user_query}" and its agent steps?`)) return;

    setIsDeleting(true);
    setError(null);
    try {
      await api.deleteResearchRun(run.id);
      setRuns((current) => {
        const remaining = current.filter((item) => item.id !== run.id);
        if (selectedRunId === run.id) {
          setSelectedRunId(remaining[0]?.id ?? null);
        }
        return remaining;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete research run");
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleClearRuns() {
    if (runs.length === 0) return;
    if (!window.confirm("Delete all research runs and agent steps?")) return;

    setIsDeleting(true);
    setError(null);
    try {
      await api.clearResearchRuns();
      setRuns([]);
      setSelectedRunId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not clear research runs");
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <section className="workspace-panel" aria-labelledby="research-heading">
      <div className="panel-header">
        <div>
          <h2 id="research-heading">Research runs</h2>
          <p>Submit a market question and inspect the mock agent trace.</p>
        </div>
        <div className="detail-badges">
          <button className="danger-button subtle" disabled={isDeleting || runs.length === 0} onClick={handleClearRuns} type="button">
            Clear history
          </button>
          <span className="status-pill">{runs.length} runs</span>
        </div>
      </div>

      <form className="query-form" onSubmit={handleSubmit}>
        <label htmlFor="research-query">Research query</label>
        <textarea
          id="research-query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Example: Which customer segments are adopting AI research tools fastest?"
          rows={4}
        />
        <button type="submit" disabled={isSubmitting || !query.trim()}>
          {isSubmitting ? "Running agent..." : "Run research"}
        </button>
      </form>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="dashboard-grid">
        <div className="run-list" aria-label="Research run list">
          {isLoading ? <p className="muted">Loading runs...</p> : null}
          {!isLoading && runs.length === 0 ? <p className="muted">No research runs yet.</p> : null}
          {runs.map((run) => (
            <div
              aria-label={`Select research run ${run.user_query}`}
              className={`run-row ${run.id === selectedRun?.id ? "selected" : ""}`}
              key={run.id}
              onClick={() => setSelectedRunId(run.id)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  setSelectedRunId(run.id);
                }
              }}
              role="button"
              tabIndex={0}
            >
              <span>{run.user_query}</span>
              <span className="run-row-footer">
                <small>{run.status}</small>
                <button className="danger-button inline" disabled={isDeleting} onClick={(event) => handleDeleteRun(event, run)} type="button">
                  Delete
                </button>
              </span>
            </div>
          ))}
        </div>

        <div className="run-detail">
          {selectedRun ? (
            <>
              <div className="detail-header">
                <div>
                  <h3>{selectedRun.user_query}</h3>
                  <p>
                    Confidence:{" "}
                    {selectedRun.confidence_score === null
                      ? "pending"
                      : `${Math.round(selectedRun.confidence_score * 100)}%`}
                  </p>
                </div>
                <div className="detail-badges">
                  <span className={`mode-badge ${selectedAiMode}`}>{selectedAiMode === "openai" ? "OpenAI mode" : "Mock mode"}</span>
                  <span className={`status-pill ${selectedRun.status}`}>{selectedRun.status}</span>
                </div>
              </div>
              <div className="answer-box">{selectedRun.final_answer || "Waiting for answer..."}</div>
              <EvidenceList evidence={selectedEvidence} />
              <AgentTimeline steps={selectedRun.steps} />
            </>
          ) : (
            <p className="muted">Select or create a run to view details.</p>
          )}
        </div>
      </div>
    </section>
  );
}

function EvidenceList({ evidence }: { evidence: RetrievalEvidence[] }) {
  return (
    <div className="evidence-list" aria-label="Retrieved evidence">
      <h4>Retrieved evidence</h4>
      {evidence.length === 0 ? <p className="muted">No evidence retrieved yet.</p> : null}
      {evidence.map((chunk) => (
        <article className="evidence-card" key={chunk.chunk_id}>
          <div className="evidence-card-header">
            <strong>{chunk.document_title}</strong>
            <span>{chunk.retrieval_mode} · {Math.round(chunk.score * 100)}%</span>
          </div>
          <p>{chunk.chunk_text}</p>
        </article>
      ))}
    </div>
  );
}

function AgentTimeline({ steps }: { steps: AgentStep[] }) {
  return (
    <div className="timeline" aria-label="Agent steps timeline">
      <h4>Agent timeline</h4>
      {steps.length === 0 ? <p className="muted">No steps recorded yet.</p> : null}
      {steps.map((step) => (
        <article className="timeline-item" key={step.id}>
          <div className="timeline-marker" />
          <div>
            <strong>{stepLabels[step.step_type]}</strong>
            <pre>{JSON.stringify(step.output_data, null, 2)}</pre>
          </div>
        </article>
      ))}
    </div>
  );
}

function getEvidence(run?: ResearchRun): RetrievalEvidence[] {
  if (!run) return [];
  const retrieveStep = run.steps.find((step) => step.step_type === "retrieve");
  return retrieveStep?.output_data.chunks ?? [];
}

function getAiMode(run?: ResearchRun): "mock" | "openai" {
  if (!run) return "mock";
  const finalStep = run.steps.find((step) => step.step_type === "final");
  const retrieveStep = run.steps.find((step) => step.step_type === "retrieve");
  return finalStep?.output_data.ai_mode ?? retrieveStep?.output_data.ai_mode ?? "mock";
}
