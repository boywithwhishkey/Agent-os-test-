import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { apiRequest, ApiError } from "./client";
import { setApiBaseUrl, setApiKey } from "./config";

describe("apiRequest", () => {
  beforeEach(() => {
    setApiBaseUrl("https://api.example.test");
    setApiKey("test-key");
    vi.stubGlobal("crypto", { randomUUID: () => "fixed-correlation-id" });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("sends the API key and correlation id, and parses a JSON response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: "task-1" }), {
        status: 201,
        headers: { "Content-Type": "application/json", "X-Correlation-ID": "fixed-correlation-id" },
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiRequest<{ id: string }>("/api/v1/tasks", { method: "POST", body: { objective: "x" } });

    expect(result).toEqual({ id: "task-1" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("https://api.example.test/api/v1/tasks");
    expect(init.headers["X-API-Key"]).toBe("test-key");
    expect(init.headers["X-Correlation-ID"]).toBe("fixed-correlation-id");
  });

  it("throws an ApiError with the backend detail message on failure", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Unauthorized" }), { status: 401 })
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiRequest("/api/v1/tasks")).rejects.toMatchObject({
      status: 401,
      detail: "Unauthorized",
      isUnauthorized: true,
    });
  });

  it("wraps network failures in a non-network ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch"))
    );

    const error = await apiRequest("/health").catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).isNetworkError).toBe(true);
  });
});
