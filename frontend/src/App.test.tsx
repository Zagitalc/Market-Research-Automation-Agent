import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const emptyListResponse = () => Promise.resolve(new Response(JSON.stringify([]), { status: 200 }));

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn(() => emptyListResponse()));
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("renders the dashboard shell", async () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: /market research automation agent/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /run research/i })).toBeDisabled();
    await waitFor(() => expect(screen.getByText(/no research runs yet/i)).toBeInTheDocument());
  });

  it("submits a research run and displays the timeline", async () => {
    const run = {
      id: 1,
      user_query: "Analyze AI research automation",
      status: "completed",
      final_answer: "Mock answer for AI research automation.",
      confidence_score: 0.78,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      steps: [
        {
          id: 1,
          research_run: 1,
          step_type: "plan",
          input_data: {},
          output_data: { plan: ["retrieve"] },
          created_at: "2026-01-01T00:00:00Z",
        },
        {
          id: 2,
          research_run: 1,
          step_type: "retrieve",
          input_data: {},
          output_data: {
            ai_mode: "mock",
            chunks: [
              {
                chunk_id: 10,
                document_id: 7,
                document_title: "Market pulse",
                chunk_text: "Automation platforms are moving toward agentic workflows.",
                score: 0.82,
                retrieval_mode: "embedding",
              },
            ],
          },
          created_at: "2026-01-01T00:00:00Z",
        },
        {
          id: 3,
          research_run: 1,
          step_type: "final",
          input_data: {},
          output_data: { ai_mode: "mock", final_answer: "Mock answer for AI research automation." },
          created_at: "2026-01-01T00:00:00Z",
        },
      ],
    };
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify(run), { status: 201 })),
    );

    render(<App />);
    await userEvent.type(screen.getByLabelText(/research query/i), "Analyze AI research automation");
    await userEvent.click(screen.getByRole("button", { name: /run research/i }));

    expect(await screen.findByText("Mock answer for AI research automation.")).toBeInTheDocument();
    expect(screen.getByText("Plan")).toBeInTheDocument();
    expect(screen.getByText("Mock mode")).toBeInTheDocument();
    expect(screen.getByText("Market pulse")).toBeInTheDocument();
    expect(screen.getByText("embedding · 82%")).toBeInTheDocument();
    expect(screen.getByText("Automation platforms are moving toward agentic workflows.")).toBeInTheDocument();
  });

  it("displays 35% confidence for a weak-evidence answer", async () => {
    const run = {
      id: 1,
      user_query: "Analyze a weak market signal",
      status: "completed",
      final_answer: "Available evidence is insufficient to answer this question confidently.",
      confidence_score: 0.35,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      steps: [],
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(new Response(JSON.stringify([run]), { status: 200 })),
    );

    render(<App />);

    expect(
      await screen.findByText(
        (_, element) => element?.tagName === "P" && element.textContent === "Confidence: 35%",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/available evidence is insufficient/i)).toBeInTheDocument();
  });

  it("adds and lists documents", async () => {
    const document = {
      id: 2,
      title: "Buyer survey",
      source_type: "survey",
      content: "Buyers want faster insight workflows.",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      chunks: [],
    };
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify(document), { status: 201 })),
    );

    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: /documents/i }));
    await userEvent.type(screen.getByLabelText(/title/i), "Buyer survey");
    await userEvent.clear(screen.getByLabelText(/source type/i));
    await userEvent.type(screen.getByLabelText(/source type/i), "survey");
    await userEvent.type(screen.getByLabelText(/content/i), "Buyers want faster insight workflows.");
    await userEvent.click(screen.getByRole("button", { name: /add document/i }));

    expect(await screen.findByText("Buyer survey")).toBeInTheDocument();
    expect(screen.getByText("Buyers want faster insight workflows.")).toBeInTheDocument();
  });

  it("deletes a document after confirmation", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const document = {
      id: 2,
      title: "Buyer survey",
      source_type: "survey",
      content: "Buyers want faster insight workflows.",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      chunks: [],
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([document]), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: /documents/i }));
    expect(await screen.findByText("Buyer survey")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /delete/i }));

    await waitFor(() => expect(screen.queryByText("Buyer survey")).not.toBeInTheDocument());
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining("/documents/2/"),
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("does not delete a document when confirmation is cancelled", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(false);
    const document = {
      id: 2,
      title: "Buyer survey",
      source_type: "survey",
      content: "Buyers want faster insight workflows.",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      chunks: [],
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([document]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: /documents/i }));
    expect(await screen.findByText("Buyer survey")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /delete/i }));

    expect(screen.getByText("Buyer survey")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("clears all documents after confirmation", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const document = {
      id: 2,
      title: "Buyer survey",
      source_type: "survey",
      content: "Buyers want faster insight workflows.",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      chunks: [],
    };
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify([document]), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify({ deleted: 1, deleted_rows: 1, details: {} }), { status: 200 })),
    );

    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: /documents/i }));
    expect(await screen.findByText("Buyer survey")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /clear all/i }));

    expect(await screen.findByText(/no documents yet/i)).toBeInTheDocument();
  });

  it("deletes a selected research run and clears the detail panel", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const run = {
      id: 1,
      user_query: "Analyze AI research automation",
      status: "completed",
      final_answer: "Mock answer for AI research automation.",
      confidence_score: 0.78,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      steps: [],
    };
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response(JSON.stringify([run]), { status: 200 }))
        .mockResolvedValueOnce(new Response(null, { status: 204 })),
    );

    render(<App />);
    expect(await screen.findAllByText("Analyze AI research automation")).toHaveLength(2);
    await userEvent.click(screen.getByRole("button", { name: /delete/i }));

    expect(await screen.findByText(/no research runs yet/i)).toBeInTheDocument();
    expect(screen.getByText(/select or create a run/i)).toBeInTheDocument();
  });

  it("clears research history after confirmation", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const run = {
      id: 1,
      user_query: "Analyze AI research automation",
      status: "completed",
      final_answer: "Mock answer for AI research automation.",
      confidence_score: 0.78,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      steps: [],
    };
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response(JSON.stringify([run]), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify({ deleted: 1, deleted_rows: 1, details: {} }), { status: 200 })),
    );

    render(<App />);
    expect(await screen.findAllByText("Analyze AI research automation")).toHaveLength(2);
    await userEvent.click(screen.getByRole("button", { name: /clear history/i }));

    expect(await screen.findByText(/no research runs yet/i)).toBeInTheDocument();
    expect(screen.getByText(/select or create a run/i)).toBeInTheDocument();
  });
});
