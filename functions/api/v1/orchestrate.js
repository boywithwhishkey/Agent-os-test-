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
    const response = await fetch("https://api.thynact.com/api/v1/orchestrate", {
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
