/**
 * Which backend this Pages Function proxies to.
 *
 * This Function is deployed to EVERY Pages environment — production, the
 * staging branch, and every feature-branch preview — from one build. A
 * hardcoded production URL therefore meant a request to
 * staging.thynact.com/api/v1/orchestrate executed a real orchestration run
 * against PRODUCTION, using whatever AGENT_OS_API_KEY that environment held.
 * Orchestration is a consequential action, so this is exactly the
 * cross-environment leak staging isolation is meant to prevent.
 *
 * Same fail-safe rule as the frontend (src/lib/api/config.ts): only the real
 * production hostname resolves to the production API; everything else falls
 * back to staging. AGENT_OS_API_BASE_URL overrides, so each Pages environment
 * can be pinned explicitly in the dashboard.
 */
function resolveApiBaseUrl(env, request) {
  const configured = env.AGENT_OS_API_BASE_URL?.trim();
  if (configured) return configured.replace(/\/+$/, "");
  let hostname = "";
  try {
    hostname = new URL(request.url).hostname;
  } catch {
    /* fall through to the staging default */
  }
  // Cloudflare serves the production deployment on the custom domain AND on
  // the project's bare pages.dev alias; previews are subdomains of that alias.
  if (hostname === "app.thynact.com" || hostname === "agent-os-test.pages.dev") {
    return "https://api.thynact.com";
  }
  return "https://api-staging.thynact.com";
}

export async function onRequestPost(context) {
  const { request, env } = context;

  if (!env.AGENT_OS_API_KEY) {
    return Response.json(
      { detail: "API authentication is not configured" },
      { status: 503 }
    );
  }

  let body;
  try {
    body = await request.text();
    JSON.parse(body);
  } catch {
    return Response.json({ detail: "Invalid JSON request body" }, { status: 400 });
  }

  try {
    const upstreamCorrelationId =
      request.headers.get("X-Correlation-ID") || crypto.randomUUID();
    const apiBaseUrl = resolveApiBaseUrl(env, request);
    const response = await fetch(`${apiBaseUrl}/api/v1/orchestrate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-API-Key": env.AGENT_OS_API_KEY,
        "X-Correlation-ID": upstreamCorrelationId
      },
      body
    });

    return new Response(await response.text(), {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("Content-Type") || "application/json",
        "X-Correlation-ID":
          response.headers.get("X-Correlation-ID") || upstreamCorrelationId
      }
    });
  } catch {
    return Response.json({ detail: "Unable to reach orchestration service" }, { status: 502 });
  }
}
