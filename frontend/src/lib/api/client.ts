import { getApiBaseUrl, getApiKey } from "./config";

export class ApiError extends Error {
  status: number;
  detail: string;
  /** Machine-readable reason from the API, when it sends one. */
  code: string | null;
  correlationId: string | null;
  isNetworkError: boolean;
  isTimeout: boolean;
  /** 401 only: the caller needs to supply a credential. */
  isUnauthorized: boolean;
  /** 403: authenticated, but not permitted. */
  isForbidden: boolean;
  /** 503: a dependency the server needs is unavailable. NOT an auth failure. */
  isUnavailable: boolean;
  isNotFound: boolean;

  constructor(opts: {
    status: number;
    detail: string;
    code?: string | null;
    correlationId: string | null;
    isNetworkError?: boolean;
    isTimeout?: boolean;
  }) {
    super(opts.detail);
    this.name = "ApiError";
    this.status = opts.status;
    this.detail = opts.detail;
    this.code = opts.code ?? null;
    this.correlationId = opts.correlationId;
    this.isNetworkError = opts.isNetworkError ?? false;
    this.isTimeout = opts.isTimeout ?? false;
    // 503 used to be folded in here, so a server with NO operator key
    // configured told the user to "Sign in" — the one action that could never
    // help, because no credential exists to supply. The three states are now
    // distinct and the UI routes them to three different messages.
    this.isUnauthorized = opts.status === 401;
    this.isForbidden = opts.status === 403;
    this.isUnavailable = opts.status === 503;
    this.isNotFound = opts.status === 404;
  }
}

function createCorrelationId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `corr-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

interface RequestOptions {
  method?: "GET" | "POST" | "DELETE" | "PATCH" | "PUT";
  body?: unknown;
  signal?: AbortSignal;
  timeoutMs?: number;
  skipAuth?: boolean;
}

const DEFAULT_TIMEOUT_MS = 30_000;

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = "GET", body, signal, timeoutMs = DEFAULT_TIMEOUT_MS, skipAuth } = options;

  const baseUrl = getApiBaseUrl().replace(/\/$/, "");
  const url = `${baseUrl}${path}`;
  const correlationId = createCorrelationId();

  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Correlation-ID": correlationId,
  };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (!skipAuth) {
    const apiKey = getApiKey();
    if (apiKey) headers["X-API-Key"] = apiKey;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  const combinedSignal = signal
    ? mergeSignals(signal, controller.signal)
    : controller.signal;

  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: combinedSignal,
    });
  } catch (err) {
    clearTimeout(timeout);
    if ((err as Error).name === "AbortError") {
      throw new ApiError({
        status: 0,
        detail: "Request timed out",
        correlationId,
        isTimeout: true,
      });
    }
    throw new ApiError({
      status: 0,
      detail: "Unable to reach the THYNACT API. Check your network or API configuration.",
      correlationId,
      isNetworkError: true,
    });
  }
  clearTimeout(timeout);

  const responseCorrelationId = response.headers.get("X-Correlation-ID") || correlationId;

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  let parsed: unknown = undefined;
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
  }

  if (!response.ok) {
    const body = parsed && typeof parsed === "object" ? (parsed as Record<string, unknown>) : null;
    // Guard against an object detail: String({...}) yields "[object Object]",
    // which would surface to the user as the entire error message.
    const rawDetail = body && "detail" in body ? body.detail : undefined;
    const detail =
      (typeof rawDetail === "string" ? rawDetail : undefined) ||
      response.statusText ||
      "Request failed";
    const code = body && typeof body.code === "string" ? body.code : null;
    throw new ApiError({
      status: response.status,
      detail,
      code,
      correlationId: responseCorrelationId,
    });
  }

  return parsed as T;
}

function mergeSignals(a: AbortSignal, b: AbortSignal): AbortSignal {
  const controller = new AbortController();
  const onAbort = () => controller.abort();
  a.addEventListener("abort", onAbort);
  b.addEventListener("abort", onAbort);
  if (a.aborted || b.aborted) controller.abort();
  return controller.signal;
}

export const api = {
  get: <T>(path: string, opts?: RequestOptions) => apiRequest<T>(path, { ...opts, method: "GET" }),
  post: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    apiRequest<T>(path, { ...opts, method: "POST", body }),
  delete: <T>(path: string, opts?: RequestOptions) =>
    apiRequest<T>(path, { ...opts, method: "DELETE" }),
};
