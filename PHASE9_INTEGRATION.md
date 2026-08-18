# Phase 9 — n8n Integration Adapter

Agent OS remains the brain. n8n is an external execution/integration layer.

## Architecture

Agent OS
→ Workflow Engine
→ Integration Adapter
→ n8n production webhook
→ Gmail / Slack / GitHub / CRM / DB / external services
→ result back to Agent OS
→ verifier / memory / next workflow step

## Configuration

```env
N8N_BASE_URL=https://your-n8n-host.example
N8N_WEBHOOK_PREFIX=webhook
N8N_WEBHOOK_AUTH_HEADER=X-Agent-Token
N8N_WEBHOOK_AUTH_VALUE=replace-me
```

Secrets must stay in environment/secret storage, never source control.

## API

`POST /api/v1/integrations/execute`

## Important design choices

- Adapter interface is provider-independent.
- n8n webhook URLs are constructed from a base URL + workflow path.
- Custom webhook authentication header is supported.
- Correlation IDs flow across Agent OS and n8n.
- Timeouts/network failures return structured errors.
- Tests use mocked HTTP and do not require a running n8n instance.

## n8n notes

For real workflows, use n8n's production webhook URL after publishing the workflow.
The test webhook URL is for development/testing.

## Future expansion

- n8n Public API client for workflow/execution administration
- signed/HMAC requests
- idempotency keys
- callback/webhook events back into Agent OS
- asynchronous executions
- queue-backed integration jobs
- integration circuit breakers
- per-connector policies and budgets

## Verify

`pytest`

Expected after Phase 9: 32 passing tests.
