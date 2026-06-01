import { FormEvent, useEffect, useMemo, useState } from "react";

import { AgentStep, ResearchRun, api } from "../api/client";

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

  return (
    <section className="workspace-panel" aria-labelledby="research-heading">
      <div className="panel-header">
        <div>
          <h2 id="research-heading">Research runs</h2>
          <p>Submit a market question and inspect the mock agent trace.</p>
        </div>
        <span className="status-pill">{runs.length} runs</span>
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
            <button
              className={`run-row ${run.id === selectedRun?.id ? "selected" : ""}`}
              key={run.id}
              onClick={() => setSelectedRunId(run.id)}
              type="button"
            >
              <span>{run.user_query}</span>
              <small>{run.status}</small>
            </button>
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
                <span className={`status-pill ${selectedRun.status}`}>{selectedRun.status}</span>
              </div>
              <div className="answer-box">{selectedRun.final_answer || "Waiting for answer..."}</div>
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
