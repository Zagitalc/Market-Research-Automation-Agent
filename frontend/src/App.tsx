import { useState } from "react";

import { DocumentsPage } from "./components/DocumentsPage";
import { ResearchDashboard } from "./components/ResearchDashboard";

type View = "research" | "documents";

export default function App() {
  const [view, setView] = useState<View>("research");

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>Market Research Automation Agent</h1>
          <p>Agentic AI scaffold for research workflows, RAG, and analyst automation.</p>
        </div>
        <nav aria-label="Primary navigation">
          <button className={view === "research" ? "active" : ""} onClick={() => setView("research")} type="button">
            Research
          </button>
          <button className={view === "documents" ? "active" : ""} onClick={() => setView("documents")} type="button">
            Documents
          </button>
        </nav>
      </header>

      <main>{view === "research" ? <ResearchDashboard /> : <DocumentsPage />}</main>
    </div>
  );
}
