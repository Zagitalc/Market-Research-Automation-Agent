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
});
