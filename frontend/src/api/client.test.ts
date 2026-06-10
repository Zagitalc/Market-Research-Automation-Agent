import { afterEach, describe, expect, it, vi } from "vitest";

describe("API client configuration", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
    vi.resetModules();
  });

  it("uses and normalizes the deployed Vite API base URL", async () => {
    vi.stubEnv("VITE_API_BASE_URL", " https://api.example.com/api/ ");
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const { api } = await import("./client");
    await api.getDocuments();

    expect(fetchMock.mock.calls[0][0]).toBe("https://api.example.com/api/documents/");
  });
});
