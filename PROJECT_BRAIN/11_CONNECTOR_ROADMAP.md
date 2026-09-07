# THYNACT connector roadmap

Status: active goal, started 2026-09-05.

This is the implementation contract for expanding THYNACT beyond the current
catalog. “Implemented” means there is a real adapter, server-side credential
configuration, canonical capability mapping, risk/approval enforcement, audit
coverage, mocked tests, and a safe connection test. “Live validated” means a
real credential was supplied and the connection test succeeded. Catalog cards
without that loop remain metadata only.

## Provider families

### Social and messaging

1. Telegram Bot API — implemented/tested send-only foundation; bot token and
   live `getMe` validation remain.
2. WhatsApp Cloud API — implemented/tested text and bounded template-message
   foundations with Meta OAuth plus a system-user-token fallback; business
   phone, richer media/templates, permissions and inbound webhook verification
   remain capability-specific follow-ons.
3. Instagram Graph API — implemented/tested text and image-publishing
   foundations with Meta OAuth plus a server-token fallback; business/creator
   account, comments and richer media/messaging remain permission- and
   capability-specific follow-ons.
4. Snapchat Marketing/Public Profile APIs — implemented/tested read-only
   organization and ad-account discovery plus bounded public-profile reads
   through OAuth 2.0 (with a legacy server-token fallback); profile access is
   allowlist-dependent and mutations/media uploads remain disabled.
5. Microsoft Teams — tested incoming-webhook send foundation; Graph OAuth and
   inbound/event capabilities remain follow-on work.
6. Discord — completed send-only webhook adapter; OAuth/bot expansion follows
   only when a concrete Discord workflow needs it.
7. Slack — OAuth identity, bounded `chat.channel.list` discovery and
   `chat.message.list` history reads, governed `chat.message.send`, and signed
   Events API ingress with replay suppression are implemented; richer event
   routing remains workflow-specific.
8. Pinterest — shared OAuth account verification and approval-gated image Pin
   publishing are implemented against API v5; board discovery, video Pins,
   analytics, and live app approval remain follow-on/credential-gated work.
9. Reddit — shared OAuth account verification and approval-gated text/link
   submission are implemented; moderation, comments, media, and live app
   validation remain follow-on/credential-gated work.
10. Google Tasks — shared Google OAuth account verification, bounded task-list
    reads, and approval-gated task creation are implemented; Google consent
    verification and live credentials remain pending.
11. Microsoft To Do — separate Microsoft OAuth account verification, bounded
    task reads, and approval-gated task creation are implemented; live Graph
    authorization remains pending.
12. Google Contacts — separate Google OAuth `contacts` scope, account
    verification, bounded contact-list reads, and approval-gated contact
    creation are implemented; live People API authorization remains pending.

### Commerce and payments

1. Shopify Admin API — implemented/tested shop/products/orders reads plus a
   governed product-create foundation; merchant OAuth, inventory, and webhook
   subscriptions follow.
2. Amazon Selling Partner API — implemented/tested LWA + SigV4 seller-identity
   foundation; marketplace-aware orders, sandbox tests, and restricted-role
   handling follow.
3. WooCommerce — implemented/tested read-only store/product/order foundation;
   approval-gated writes follow.
4. Stripe — implemented/tested account/payment/subscription reads plus an
   approval-gated refund capability; customer operations remain follow-on work.
5. Razorpay — API credentials, payment/order reads and approval-gated refunds.

### Daily productivity

Google Gmail/Calendar/Drive/Sheets, LinkedIn, Microsoft Outlook/Calendar/OneDrive, Notion,
GitHub/GitLab, Linear (issue list/create/update implemented), Jira, Dropbox, Todoist, Trello, Asana, Zoom, and
calendar/meeting providers are added through the same OAuth/API families.

## Delivery phases

### Phase 1 — messaging foundation

Implement shared token/tenant-safe storage and webhook verification, then
Telegram, WhatsApp Cloud, Instagram, and Teams in that order. Each provider
gets one read/verify capability and one governed send capability first; media,
threads, templates, and inbound events follow as separate capabilities.

### Phase 2 — commerce foundation

Implement Shopify and Stripe against sandbox/test modes first, then Amazon
SP-API and WooCommerce. No production order, inventory, refund, or payment
mutation is enabled without explicit high-risk approval and an audit receipt.

### Phase 3 — remaining daily-life providers

Add the highest-value providers from the current catalog and user demand,
reusing the same adapter, OAuth, webhook, status, and test harness rather than
creating one-off integrations.

## Acceptance checklist for every connector

- Provider credentials are server-side only; no secrets in frontend storage,
  logs, errors, fixtures, Project Brain, or git.
- OAuth state is single-use and expires; state digests and access/refresh tokens
  are tenant-scoped in PostgreSQL when durable OAuth storage is enabled.
  `AGENT_OS_API_KEYS_JSON` selects the tenant from server-held keys, and the
  public callback restores the tenant from its validated state claim. Never
  accept a client-supplied tenant header. Multi-user rollout still requires
  credential-backed staging smoke tests and key-rotation runbooks.
- Verified webhook callbacks are routed only by the server-held
  `AGENT_OS_WEBHOOK_TENANT_MAP` using provider/account identifiers; account
  routes take precedence over provider fallbacks, and unknown or conflicting
  routes fail closed. The resolved tenant travels in the queue job and is
  restored around worker execution. `AGENT_OS_WEBHOOK_WORKFLOW_MAP` may pin a
  tenant to a workflow with a `tenant:provider` key, which takes precedence
  over the provider fallback. Do not use a tenant header or payload field as
  an authority source.
  Meta, WhatsApp, and Instagram callbacks retain provider-specific routes and
  normalized event identities; `/meta` remains a backward-compatible alias.
- API-token connectors may use `AGENT_OS_CONNECTOR_CREDENTIALS_JSON`, keyed by
  stable tenant id and provider env-name. A non-default tenant without a
  scoped credential is reported as not configured rather than inheriting the
  operator's token. Values remain server-side and are never serialized.
  This selector is wired through AI, automation, chat webhook, cloud,
  deployment, data, social, commerce, and productivity adapters; infrastructure
  database/queue settings remain deployment-scoped by design.
  OAuth client registrations remain deployment-scoped, but tenant-specific
  routing identifiers use the same map: Jira `JIRA_CLOUD_ID` and Salesforce
  `SALESFORCE_INSTANCE_URL` are isolated with their OAuth connections. A tenant
  without its routing identifier fails closed.
- Adapter accepts canonical capability arguments only and never an arbitrary
  provider URL or operation name from an agent.
- Read, write, and high-risk operations use the shared capability risk model;
  high-risk operations require human approval and produce an audit row.
- Timeouts, rate limits, provider errors, retries, and redaction are tested;
  canonical broker execution now enforces timeout/retry/rate/circuit controls
  with tenant-isolated keys before calling an adapter; automatic retries are
  restricted to READ capabilities so writes are not blindly replayed.
- Mocked contract tests pass; provider sandbox tests pass where available;
  live validation is recorded only after a real credential-backed call.
- The connector is pushed in its own verified commit and the worktree is
  clean.

## Current baseline

THYNACT now has 48 catalog entries. All forty-eight have adapters and tests; PostgreSQL
and Redis are the only live-validated providers. The remaining implemented
providers are credential/auth gated. There are no catalog-only entries left;
the next work is capability depth, multi-user tenant isolation, provider-specific
event expansion, sandbox validation, and live credential checks. OAuth refresh-on-401,
encrypted expiry metadata, and verified Meta / Telegram webhook ingress with
queue handoff and replay suppression are now implemented and tested; live
provider refresh/webhook delivery is still credential-gated.
Verified webhook jobs now also carry a server-resolved tenant id through the
queue/worker path; multi-tenant callback smoke tests and live account routing
remain pending isolated staging credentials.
LinkedIn now has a member OIDC identity and bounded text-post foundation; the
`w_member_social` product permission and live app credentials remain pending.
Google Gmail/Calendar/Drive/Sheets now share one OAuth client configuration and
have bounded identity/list/range adapters plus Drive file-content reads; Sheets
row appends and other write capabilities remain separately gated.
Jira now has the same read-only OAuth foundation with a server-configured cloud
id; issue mutations remain a separate approval-gated capability.
Dropbox and OneDrive now have scoped OAuth identity/file-list/file-content
foundations; file writes/deletes remain separately gated. Dropbox's OAuth scope
now includes `files.content.read`, so existing connections must re-authorize.
HubSpot now has an OAuth identity/contact-list foundation; CRM mutations remain
separately gated.
Linear now has fixed GraphQL identity/issue-list operations plus governed
`tracker.issue.create` and `tracker.issue.update` mutations. Those writes remain
credential-gated and require the shared broker approval/audit path at runtime.
The broker is now exposed through authenticated canonical capability execution
and single-use approval endpoints; callers cannot select a provider, and every
refusal or provider result is correlated and audited.
Google Drive, Dropbox, and OneDrive now have bounded `files.file.read`
operations; Dropbox connections must re-authorize for the expanded content-read
scope.
Render now has fixed service listing and governed deploy-trigger operations;
live use requires a staging-safe service id and API key.
Cloudflare now has fixed account and DNS-record reads; live use requires a
token with the corresponding Zone/DNS read permissions.
Vercel now has an approval-gated deploy-hook trigger; live use requires a
staging-safe, host-validated `VERCEL_DEPLOY_HOOK_URL`.
OpenAI, Anthropic, and Gemini now have bounded model-list/completion adapter
paths through the canonical `ai.*` capabilities; completion remains approval
gated and no provider credentials were available for live validation.
Discord and Teams are intentionally send-only webhook connectors in the
catalog; identity/list capabilities require a future OAuth or bot adapter.
Supabase now supports bounded approval-gated writes to its one configured
PostgREST table in addition to record reads; Auth/Storage remain separate
capabilities until their own credentials and policies are wired.
n8n, Make, and Zapier now expose bounded canonical
`automation.workflow.trigger` routes through the broker; standalone execution
read is not claimed because webhook providers do not expose a shared read API.
Todoist now has bounded `productivity.task.list` and approval-gated
`productivity.task.create` routes with a server-side API token and request
idempotency; live credentials remain unconfigured.
Asana now has the same canonical task routes through a fixed configured
workspace and Bearer token; workflow input cannot change workspace scope and
live credentials remain unconfigured.
Outlook now has the shared Microsoft OAuth configuration plus bounded Graph
mail listing/read, draft creation, approval-gated send, and calendar
list/create/update/delete routes. Existing connections must re-authorize for
the expanded `Mail.ReadWrite` scope; no Microsoft OAuth credentials were
available for live validation.
Trello now has a fixed-board/list API-key adapter for account identity,
bounded open-card listing, and approval-gated card creation through the
canonical productivity task capabilities; live Trello credentials remain
unconfigured.
Zoom now has shared OAuth identity, bounded scheduled-meeting reads with
cursor support, and approval-gated scheduled-meeting creation through the
canonical `meeting.session.*` capabilities; live Zoom credentials remain
unconfigured. Its signed webhook endpoint, challenge response, replay window,
queue deduplication, and canonical event normalization are implemented; the
webhook secret remains unconfigured for live delivery.
Razorpay now has fixed `commerce.payment.list` and `commerce.order.list`
operations plus approval-gated `commerce.refund.create`; the key pair stays
server-side and live payment credentials remain unconfigured.
Salesforce now has an OAuth identity/contact-list foundation with a
server-configured instance URL; CRM mutations remain separately gated.
Supabase now has a server-configured table read foundation, and Zapier has a
fixed HTTPS webhook trigger foundation.
Slack now also has an OAuth-backed, approval-gated message-send capability with
bounded channel/text arguments and secret-safe provider errors. It also has a
bounded OAuth-backed `conversations.history` read with cursor pagination;
provider credentials and live Slack validation remain gated. Channel discovery
uses the fixed `conversations.list` endpoint with an allowlisted type filter.
Its catalog-declared `identity.account.read` capability now also routes through
the fixed `auth.test` endpoint and filters the returned identity fields.

## Operator prerequisites

The engineering work can proceed with mocked/sandbox tests. Live validation
requires the operator to create provider apps, configure redirect/webhook URLs,
complete platform review/allowlisting where required, and provide credentials
through the deployment secret manager. Never paste those credentials into chat
or commit them to the repository.
