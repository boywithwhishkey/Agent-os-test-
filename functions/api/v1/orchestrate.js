export async function onRequestPost(context) {
  const { request, env } = context;

  const body = await request.text();

  const response = await fetch(
    "https://api.thynact.com/api/v1/orchestrate",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-API-Key": env.AGENT_OS_API_KEY
      },
      body
    }
  );

  return new Response(await response.text(), {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") || "application/json"
    }
  });
}
