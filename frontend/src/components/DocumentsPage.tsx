import { FormEvent, useEffect, useState } from "react";

import { DocumentRecord, api } from "../api/client";

export function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState("report");
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;

    api
      .getDocuments()
      .then((data) => {
        if (!ignore) setDocuments(data);
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim() || !content.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const document = await api.createDocument({
        title: title.trim(),
        source_type: sourceType.trim() || "note",
        content: content.trim(),
      });
      setDocuments((current) => [document, ...current]);
      setTitle("");
      setSourceType("report");
      setContent("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create document");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDeleteDocument(document: DocumentRecord) {
    if (!window.confirm(`Delete "${document.title}" and its chunks?`)) return;

    setIsDeleting(true);
    setError(null);
    try {
      await api.deleteDocument(document.id);
      setDocuments((current) => current.filter((item) => item.id !== document.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete document");
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleClearDocuments() {
    if (documents.length === 0) return;
    if (!window.confirm("Delete all documents and their chunks?")) return;

    setIsDeleting(true);
    setError(null);
    try {
      await api.clearDocuments();
      setDocuments([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not clear documents");
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <section className="workspace-panel" aria-labelledby="documents-heading">
      <div className="panel-header">
        <div>
          <h2 id="documents-heading">Documents</h2>
          <p>Add source material for the mock retrieval layer.</p>
        </div>
        <div className="detail-badges">
          <button className="danger-button subtle" disabled={isDeleting || documents.length === 0} onClick={handleClearDocuments} type="button">
            Clear all
          </button>
          <span className="status-pill">{documents.length} docs</span>
        </div>
      </div>

      <form className="document-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            Title
            <input value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <label>
            Source type
            <input value={sourceType} onChange={(event) => setSourceType(event.target.value)} />
          </label>
        </div>
        <label>
          Content
          <textarea value={content} onChange={(event) => setContent(event.target.value)} rows={5} />
        </label>
        <button type="submit" disabled={isSubmitting || !title.trim() || !content.trim()}>
          {isSubmitting ? "Adding..." : "Add document"}
        </button>
      </form>

      {error ? <div className="error-banner">{error}</div> : null}
      {isLoading ? <p className="muted">Loading documents...</p> : null}

      <div className="document-list">
        {!isLoading && documents.length === 0 ? <p className="muted">No documents yet.</p> : null}
        {documents.map((document) => (
          <article className="document-card" key={document.id}>
            <div>
              <div>
                <h3>{document.title}</h3>
                <span>{document.source_type}</span>
              </div>
              <button className="danger-button" disabled={isDeleting} onClick={() => handleDeleteDocument(document)} type="button">
                Delete
              </button>
            </div>
            <p>{document.content}</p>
            <small>{document.chunks.length} chunk(s)</small>
          </article>
        ))}
      </div>
    </section>
  );
}
