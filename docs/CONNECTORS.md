# THYNACT — Connector Status and Expansion Plan

Generated from `app/integrations/catalog.py` and verified against runtime on
2026-08-31. Status vocabulary is the project's own (see `CLAUDE.md` §6);
`LIVE_VALIDATED` means a real provider/backend call succeeded through the
governed path, never that an adapter, catalog row, UI card or passing unit
test exists.

## 1. Headline, stated honestly

- Catalog entries: **28**. With a real adapter: **13**. Catalog-only: **15**.
- `LIVE_VALIDATED`: **2** — `postgresql` and `redis`.
- **Customer-facing SaaS connectors live-validated: 0.**

That distinction matters. PostgreSQL and Redis are *THYNACT's own
infrastructure*, not third-party accounts a customer connects. They are
correctly described as such in the catalog, but they must never be counted
toward "integrations we support" — doing so would inflate the number with
things every deployment already needs. Real connector validation begins when a
provider credential exists and a governed call to that provider succeeds.

## 2. Current catalog

| Category | Provider | State | Transport | Blocker |
|---|---|---|---|---|
| ai | anthropic | IMPLEMENTED | api | CREDENTIAL_REQUIRED (`ANTHROPIC_API_KEY`) |
| ai | gemini | IMPLEMENTED | api | CREDENTIAL_REQUIRED (`GEMINI_API_KEY`) |
| ai | openai | IMPLEMENTED | api | CREDENTIAL_REQUIRED (`OPENAI_API_KEY`) |
| automation | make | IMPLEMENTED | webhook | CREDENTIAL_REQUIRED (`MAKE_WEBHOOK_URL`) |
| automation | n8n | IMPLEMENTED | webhook | CREDENTIAL_REQUIRED (`N8N_BASE_URL`) |
| automation | zapier | CATALOG_ONLY | webhook | NOT_IMPLEMENTED |
| data | postgresql | **LIVE_VALIDATED** | api | — (own infrastructure) |
| data | redis | **LIVE_VALIDATED** | api | — (own infrastructure) |
| data | supabase | CATALOG_ONLY | api | NOT_IMPLEMENTED |
| developer | cloudflare | IMPLEMENTED | api | CREDENTIAL_REQUIRED (`CLOUDFLARE_API_TOKEN`) |
| developer | github | IMPLEMENTED | oauth | AUTH_REQUIRED |
| developer | gitlab | IMPLEMENTED | oauth | AUTH_REQUIRED |
| developer | render | IMPLEMENTED | api | CREDENTIAL_REQUIRED (`RENDER_API_KEY`) |
| developer | vercel | CATALOG_ONLY | api | NOT_IMPLEMENTED |
| google | gmail, google_calendar, google_drive | CATALOG_ONLY | oauth | NOT_IMPLEMENTED |
| productivity | notion | IMPLEMENTED | oauth | AUTH_REQUIRED |
| productivity | slack | IMPLEMENTED | oauth | AUTH_REQUIRED |
| productivity | discord, jira, linear, teams | CATALOG_ONLY | webhook/oauth/api | NOT_IMPLEMENTED |
| other | dropbox, hubspot, onedrive, salesforce, stripe | CATALOG_ONLY | oauth/api | NOT_IMPLEMENTED |

Every implemented non-webhook adapter is **read/verify only** — `execute()` is
deliberately unsupported. None of them can yet take a consequential action, so
"GitHub is implemented" means "we can verify a token", not "we can open a PR".

## 3. The real bottleneck is not adapter count

`CatalogSpec.capabilities` is a list of **human-readable display strings**
(`"Trigger workflow"`, `"Verify API key"`). There is **no canonical capability
layer**: nothing in the codebase defines `mail.message.send`,
`commerce.orders.list` or `ads.budget.update`, and the broker does not route by
capability intent. Agents would reason about provider-specific tools.

Consequently, adding adapters now multiplies provider-specific code rather than
compounding. The highest-value connector work, in order:

1. **Canonical capability namespace + registry** — capability id, input/output
   schema, risk class, approval requirement. This is the thing every later
   connector reuses.
2. **Broker routing by capability**, with transport preference
   OFFICIAL_MCP → verified/trusted MCP → managed connector → existing native →
   new native, and deny-by-default for unknown MCP tools.
3. **Consequential-action governance per capability** — a `*.send`, `*.publish`,
   `*.delete`, `*.budget.update` must be policy- and approval-gated by
   classification, not by remembering to guard each adapter.
4. **A staging safety policy** so a staging tenant cannot perform real
   consequential actions; prefer provider sandbox/test modes where they exist.
5. Only then: breadth, two or three providers at a time, each proven
   `LIVE_VALIDATED` before the next.

## 4. Intended provider universe — classification

From the Master Guide. **Do not build these speculatively**; this exists so
that when a provider is requested the classification is already known.

| Category | Representative providers | Realistic near-term class |
|---|---|---|
| Communication | Slack, Teams, Discord, Telegram, Twilio, SendGrid, Brevo, Mailchimp, Intercom, Zendesk | Slack IMPLEMENTED (auth pending); rest NOT_IMPLEMENTED |
| Google | Gmail, Calendar, Drive, Docs, Sheets, Analytics, Search Console, BigQuery | CATALOG_ONLY. One OAuth app can likely serve gmail/calendar/drive with different scopes — verify before assuming three registrations |
| Microsoft | Outlook, OneDrive, SharePoint, Teams, Excel, Azure, Dynamics | NOT_IMPLEMENTED; Graph consent is tenant-admin gated → PROVIDER_APPROVAL_REQUIRED for many scopes |
| Developer / cloud | GitHub, GitLab, Cloudflare, Render, Vercel, Supabase, Sentry, AWS/GCP/Azure | Four IMPLEMENTED; strongest area |
| Productivity | Linear, Jira, Trello, Asana, ClickUp, Airtable, Notion | Notion IMPLEMENTED (auth pending) |
| CRM / sales | Salesforce, HubSpot, Zoho, Pipedrive | CATALOG_ONLY. Salesforce requires a connected app; HubSpot requires app review for public apps → PROVIDER_APPROVAL_REQUIRED |
| Ecommerce | Shopify, WooCommerce, Amazon SP-API, eBay, Etsy, BigCommerce | NOT_IMPLEMENTED. Amazon SP-API requires developer registration and appstore approval → PROVIDER_APPROVAL_REQUIRED |
| Indian marketplaces | Flipkart, Meesho, Myntra, AJIO, IndiaMART | Seller APIs are partner-gated and not openly self-serve → RESTRICTED / PROVIDER_APPROVAL_REQUIRED. Never fabricate access |
| Ads | Meta, Google, TikTok, LinkedIn, Snapchat, Reddit, Microsoft, Amazon | NOT_IMPLEMENTED. All require app review and most gate spend scopes → PROVIDER_APPROVAL_REQUIRED. **Read-first**; budget changes are consequential |
| Social / content | Instagram, Facebook Pages, Threads, TikTok, YouTube, X, LinkedIn, Pinterest, Reddit | NOT_IMPLEMENTED. Meta/TikTok/X require app review; X's API is paid → PROVIDER_APPROVAL_REQUIRED |
| Payments / finance | Stripe, PayPal, Square, Razorpay, Cashfree, QuickBooks, Xero | CATALOG_ONLY (stripe). **Never move real money to validate**; use provider test modes only |
| Databases / data | PostgreSQL, MySQL, MongoDB, Snowflake, BigQuery, Pinecone, Qdrant | Postgres/Redis live. External DBs must default to **read-only** |
| Storage | Drive, OneDrive, Dropbox, Box, S3, R2 | CATALOG_ONLY |
| Analytics | GA4, Search Console, Mixpanel, Amplitude, PostHog | NOT_IMPLEMENTED |
| Support | Zendesk, Intercom, Freshdesk, Gorgias | NOT_IMPLEMENTED |
| Automation | n8n, Zapier, Make, Pipedream | n8n + make IMPLEMENTED. Never expose an unrestricted "run any workflow" tool — map to governed capabilities |
| Custom / internal | REST, GraphQL, webhooks, private MCP, customer databases | Requires the capability layer first |

## 5. Rules that do not change

- MCP-first, not MCP-only; never choose an unsafe MCP server to write less code.
- External content — emails, pages, issues, documents, CRM records, MCP tool
  output — is **untrusted data** and must never become instructions.
- External database capabilities default to read-only.
- A connector is not "working" because a registry row, adapter, mock, test or
  UI card exists.
