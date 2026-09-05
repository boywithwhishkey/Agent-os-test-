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
2. WhatsApp Cloud API — implemented/tested text foundation; Meta app/OAuth or system-user token, business phone,
   message templates and inbound webhook verification.
3. Instagram Graph API — implemented/tested text foundation; Meta OAuth, business/creator account, publishing,
   comments and messaging where the approved permissions allow it.
4. Snapchat Marketing/Public Profile APIs — implemented/tested read-only
   organization foundation; OAuth, ad/profile scopes, and allowlist-dependent
   features remain separate from generally available calls.
5. Microsoft Teams — tested incoming-webhook send foundation; Graph OAuth and
   inbound/event capabilities remain follow-on work.
6. Discord — completed send-only webhook adapter; OAuth/bot expansion follows
   only when a concrete Discord workflow needs it.
7. Slack — existing OAuth identity adapter; governed message actions remain a
   separate implementation batch.

### Commerce and payments

1. Shopify Admin API — implemented/tested read-only shop/products/orders
   foundation; merchant OAuth, inventory, and webhook subscriptions follow.
2. Amazon Selling Partner API — implemented/tested LWA + SigV4 seller-identity
   foundation; marketplace-aware orders, sandbox tests, and restricted-role
   handling follow.
3. WooCommerce — implemented/tested read-only store/product/order foundation;
   approval-gated writes follow.
4. Stripe — implemented/tested read-only account/payment/subscription
   foundation; customers and refunds require separate approved capabilities.
5. Razorpay — API credentials, payment/order reads and approval-gated refunds.

### Daily productivity

Google Gmail/Calendar/Drive, Microsoft Outlook/Calendar/OneDrive, Notion,
GitHub/GitLab, Linear (read-only foundation implemented), Jira, Dropbox, Todoist, Trello, Asana, Zoom, and
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
- OAuth state is single-use and expires; access/refresh tokens are encrypted
  at rest before multi-user production use.
- Adapter accepts canonical capability arguments only and never an arbitrary
  provider URL or operation name from an agent.
- Read, write, and high-risk operations use the shared capability risk model;
  high-risk operations require human approval and produce an audit row.
- Timeouts, rate limits, provider errors, retries, and redaction are tested.
- Mocked contract tests pass; provider sandbox tests pass where available;
  live validation is recorded only after a real credential-backed call.
- The connector is pushed in its own verified commit and the worktree is
  clean.

## Current baseline

THYNACT now has 35 catalog entries. Thirty-two have adapters and tests; PostgreSQL
and Redis are the only live-validated providers. The remaining implemented
providers are credential/auth gated. Three catalog entries still need real
adapters: Zapier, Supabase, and Salesforce.
Google Gmail/Calendar/Drive now share one OAuth client configuration and have
read-only identity/list adapters; write capabilities remain separately gated.
Jira now has the same read-only OAuth foundation with a server-configured cloud
id; issue mutations remain a separate approval-gated capability.
Dropbox and OneDrive now have scoped OAuth identity/file-list foundations;
file mutations remain separately gated.
HubSpot now has an OAuth identity/contact-list foundation; CRM mutations remain
separately gated.

## Operator prerequisites

The engineering work can proceed with mocked/sandbox tests. Live validation
requires the operator to create provider apps, configure redirect/webhook URLs,
complete platform review/allowlisting where required, and provide credentials
through the deployment secret manager. Never paste those credentials into chat
or commit them to the repository.
