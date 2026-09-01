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

  it("keeps 401, 403 and 503 as three distinct states", async () => {
    // 503 used to be folded into isUnauthorized, so a server with no operator
    // key configured told the user to "Sign in" — the one action that cannot
    // help, because no credential exists for them to supply.
    const cases = [
      { status: 401, flag: "isUnauthorized" },
      { status: 403, flag: "isForbidden" },
      { status: 503, flag: "isUnavailable" },
    ] as const;

    for (const { status, flag } of cases) {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(
          new Response(JSON.stringify({ detail: "nope" }), { status })
        )
      );
      const error = (await apiRequest("/api/v1/tools").catch((e) => e)) as ApiError;

      expect(error[flag]).toBe(true);
      for (const other of cases) {
        if (other.flag !== flag) expect(error[other.flag]).toBe(false);
      }
    }
  });

  it("exposes the machine-readable error code from the API", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ detail: "API authentication is not configured", code: "auth_not_configured" }),
          { status: 503 }
        )
      )
    );

    const error = (await apiRequest("/api/v1/tools").catch((e) => e)) as ApiError;
    expect(error.code).toBe("auth_not_configured");
    expect(error.isUnauthorized).toBe(false);
  });

  it("never renders an object detail as [object Object]", async () => {
    // FastAPI nests a dict detail unless the server flattens it. If that ever
    // regresses, the user must not see "[object Object]" as the error message.
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: { detail: "Unauthorized", code: "x" } }), {
          status: 401,
        })
      )
    );

    const error = (await apiRequest("/api/v1/tools").catch((e) => e)) as ApiError;
    expect(error.detail).not.toContain("[object Object]");
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
