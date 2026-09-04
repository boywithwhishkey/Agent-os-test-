/**
 * English — the canonical catalogue and the fallback for every other locale.
 *
 * This file defines the SHAPE. `Translations` is derived from it, so a missing
 * or misspelled key in any other locale is a TypeScript error rather than a raw
 * key rendered to a user. Add keys here first.
 *
 * `{name}` placeholders are interpolated; never build sentences by
 * concatenation, because word order is not the same in every language.
 * `_one` / `_other` suffixes are plural forms selected by Intl.PluralRules.
 */
export const en = {
  common: {
    save: "Save",
    cancel: "Cancel",
    close: "Close",
    delete: "Delete",
    retry: "Retry",
    refresh: "Refresh",
    viewAll: "View all",
    search: "Search",
    loading: "Loading…",
    signIn: "Sign in",
    authenticate: "Authenticate",
    unavailable: "Unavailable",
    offline: "Offline",
    noAccess: "No access",
    yes: "Yes",
    no: "No",
    optional: "Optional",
    required: "Required",
    copy: "Copy",
    copied: "Copied",
    back: "Back",
    next: "Next",
    done: "Done",
    operator: "Operator",
    apiKeyConfigured: "API key configured",
    noApiKeySet: "No API key set",
    connections: "Connections",
    clearSession: "Clear session",
    allOutcomes: "All outcomes",
    allScopes: "All scopes",
    allIntegrations: "All integrations",
    success: "Success",
    failed: "Failed",
    approvalRequired: "Approval required",
    selectTool: "Select a tool…",
    approvedBy: "Approved by",
    sessionGrants: "This session's grants",
    sessionTasks: "This session's tasks",
    events: "Events",
    priorityLow: "Low",
    priorityNormal: "Normal",
    priorityHigh: "High",
    priorityCritical: "Critical",
    notConfigured: "Not configured",
    saveConfiguration: "Save configuration",
    appearance: "Appearance",
    about: "About",
    displayName: "Display name",
    none: "None",
    executionStages: "Execution stages",
    finalAnswer: "Final answer",
    finalSynthesis: "Final synthesis",
    reviewerIssues: "Reviewer issues",
    autonomousSpecialists: "Autonomous specialists",
    resumePausedSteps: "Resume paused steps",
    idempotencyKey: "Idempotency key",
  },

  language: {
    label: "Language",
    switchTo: "Switch to {language}",
    current: "Current language: {language}",
  },

  theme: {
    label: "Theme",
    change: "Change theme",
    dark: "Dark",
    light: "Light",
    system: "System",
  },

  nav: {
    groups: {
      overview: "Overview",
      execution: "Execution",
      workflows: "Workflows",
      knowledge: "Knowledge",
      operations: "Operations",
      system: "System",
    },
    items: {
      dashboard: "Dashboard",
      productOverview: "Product Overview",
      tasks: "Tasks",
      orchestrate: "Orchestrate",
      autonomousRuns: "Autonomous Runs",
      agents: "Agents",
      workflows: "Workflows",
      workflowRuns: "Workflow Runs",
      approvals: "Approvals",
      memory: "Memory",
      runtime: "Runtime",
      tools: "Tools",
      integrations: "Integrations",
      auditLogs: "Audit Logs",
      health: "Health",
      settings: "Settings",
      privacy: "Privacy & Policy",
    },
    openNavigation: "Open navigation",
    expandSidebar: "Expand sidebar",
    collapseSidebar: "Collapse sidebar",
  },

  topbar: {
    searchPlaceholder: "Search or jump to…",
    apiOnline: "API online",
    apiOffline: "API offline",
    connecting: "Connecting",
    degraded: "Degraded",
    keyNeeded: "Key needed",
    checkingApi: "Checking the API…",
    apiUnreachable: "The API could not be reached. Check the base URL in Settings.",
    storageEphemeral: "Storage is ephemeral — data is lost when the API restarts.",
    nonProduction: "Non-production deployment ({environment})",
  },

  states: {
    loading: "Loading…",
    nothingYet: "Nothing yet this session.",
    somethingWentWrong: "Something went wrong",
    unexpectedError: "Unexpected error",
    timedOut: "The request timed out",
    cantReachApi: "Can't reach the API",
    networkHint: "Check your network or API configuration.",
    tried: "Tried: {url}",
    notFound: "Not found",
    authRequiredTitle: "Operator authentication required",
    authRequiredBody: "This view becomes available after authentication — {detail}",
    serviceUnavailableTitle: "Service temporarily unavailable",
    permissionDeniedTitle: "Permission denied",
    correlationId: "Correlation ID: {id}",
  },

  /**
   * Display text for the API's MACHINE error codes. Keyed on the stable `code`
   * field, so the wire contract is untouched and no backend prose is passed
   * through a translator.
   */
  errorCodes: {
    auth_not_configured: "This deployment has no operator key configured.",
    authentication_required: "Sign in with an operator key to continue.",
    authentication_invalid: "That operator key was not accepted.",
  },

  dashboard: {
    apiStatus: "API status",
    online: "Online",
    offline: "Offline",
    degraded: "Degraded",
    toolsAvailable: "Tools available",
    auditEvents: "Audit events",
    thisSession: "This session",
    sessionHint: "Tasks, runs & executions started here",
    ephemeralHint: "Ephemeral storage — data is lost on restart",
    keyRequiredToList: "Operator key required to {action}",
    notPermittedTo: "This key is not permitted to {action}",
    actionListTools: "list tools",
    actionReadAudit: "read the audit log",
    recentAudit: "Recent audit activity",
    noAuditYet: "No audit events yet",
    auditHint: "Tool executions and approval checks will show up here.",
    quickActions: "Quick actions",
    startOrchestration: "Start orchestration",
    runAutonomous: "Run autonomous objective",
    createTask: "Create a task",
    sessionActivity: "Session activity",
    tasks: "Tasks",
    workflowRuns: "Workflow runs",
    runtimeExecutions: "Runtime executions",
    view: "View",
    heroLead: "Your control centre",
    heroBody:
      "Give THYNACT an objective and it plans, verifies and executes — every consequential step gated by policy and written to the audit trail.",
    heroPrimary: "Start orchestration",
    heroSecondary: "See what it does",
    exploreTitle: "Explore",
    explore: {
      overview: {
        title: "Product Overview",
        body: "Every capability that is live today, each one linking to the surface that runs it.",
      },
      integrations: {
        title: "Connectors",
        body: "Browse the connector catalogue and see what is connected, waiting on setup, or not built yet.",
      },
      about: {
        title: "About THYNACT",
        body: "Why it exists, how work moves through it, and what it holds to.",
      },
      health: {
        title: "System Health",
        body: "Live status straight from the backend, including storage durability.",
      },
    },
    sessionEmptyHint: "Anything you start in this tab appears here.",
  },

  // Canonical capability labels, keyed by the capability id the backend
  // reports. The ids themselves are machine values and are never
  // translated; only the human-readable label is. The API also sends an
  // English label, which is the fallback when a key is missing here.
  capabilities: {
    identity: {
      account: {
        read: "Read the connected account",
      },
    },
    mail: {
      message: {
        list: "List messages",
        read: "Read message contents",
        send: "Send mail",
      },
      draft: {
        create: "Create a draft",
      },
    },
    calendar: {
      event: {
        list: "List calendar events",
        create: "Create a calendar event",
        update: "Update a calendar event",
        delete: "Delete a calendar event",
      },
    },
    files: {
      file: {
        list: "List files",
        read: "Read file contents",
        write: "Create or update a file",
        delete: "Delete a file",
      },
    },
    chat: {
      message: {
        list: "Read channel messages",
        send: "Post a message",
      },
    },
    docs: {
      page: {
        read: "Read pages",
        write: "Create or update a page",
      },
    },
    tracker: {
      issue: {
        list: "List issues",
        create: "Create an issue",
        update: "Update an issue",
      },
    },
    repo: {
      metadata: {
        read: "Read repository metadata",
      },
      content: {
        read: "Read repository contents",
      },
      issue: {
        create: "Open an issue or pull request",
      },
      branch: {
        merge: "Merge a branch",
      },
    },
    automation: {
      run: {
        read: "Read an execution result",
      },
      workflow: {
        trigger: "Trigger an external workflow",
      },
    },
    ai: {
      model: {
        list: "List available models",
      },
      completion: {
        create: "Run a model completion",
      },
    },
    data: {
      record: {
        read: "Read records",
        write: "Write records",
      },
      search: {
        semantic: "Semantic search",
      },
    },
    queue: {
      job: {
        read: "Read queued jobs",
        enqueue: "Enqueue a job",
      },
    },
    crm: {
      contact: {
        list: "List CRM contacts",
        update: "Update a CRM contact",
      },
      deal: {
        list: "List deals",
      },
      ticket: {
        list: "List tickets",
      },
    },
    commerce: {
      payment: {
        list: "List payments",
      },
      subscription: {
        list: "List subscriptions",
      },
      refund: {
        create: "Issue a refund",
      },
    },
    cloud: {
      service: {
        read: "Read service status",
      },
      dns: {
        read: "Read DNS and edge configuration",
      },
      deploy: {
        trigger: "Trigger a deployment",
      },
    },
    auth: {
      user: {
        list: "List authenticated users",
      },
    },
  },

  pages: {
    overview: {
      title: "Product Overview",
      heroTitle: "An agent platform that thinks first, then acts under your control.",
      heroBody:
        "THYNACT plans, delegates, verifies and executes — with every consequential action gated by policy, recorded in an audit trail, and traceable back to the request that caused it.",
      whatItDoes: "What it does",
      everyItemLinks: "Every item links to the live surface",
      howItStaysTrustworthy: "How it stays trustworthy",
      trustworthyBody:
        "Autonomy is only useful if it is bounded. These are enforced in code, not described in a policy document.",
      startOrchestration: "Start an orchestration",
      browseConnectors: "Browse connectors",
      connectors: "Connectors",
      viewIntegrations: "View integrations",
      pillars: {
        reason: {
          title: "Reason before it acts",
          body: "Every request is routed by complexity, confidence and risk. Simple asks stay on a fast deterministic path; only work that genuinely needs planning or multiple specialists pays for it.",
          action: "Orchestrate",
        },
        threeRole: {
          title: "Three-role orchestration",
          body: "Researcher, builder and reviewer run as a coordinated plan with a real parallelism limit, so complex objectives are decomposed and checked rather than answered in one pass.",
          action: "Autonomous runs",
        },
        workflow: {
          title: "Durable workflow engine",
          body: "A visual DAG builder with dependency validation, retries, timeouts, conditions and approval gates. Runs are persisted and can be resumed past a pause.",
          action: "Build a workflow",
        },
        tools: {
          title: "Governed tool execution",
          body: "Tools carry a risk level. Read tools run freely; write and high-risk tools require a single-use approval grant that cannot be self-issued by the model.",
          action: "Tool registry",
        },
        memory: {
          title: "Semantic + lexical memory",
          body: "Hybrid retrieval over pgvector with real relevance scoring — semantic similarity, lexical match and an importance weight — not a keyword search wearing a new name.",
          action: "Search memory",
        },
        runtime: {
          title: "Runtime you can see",
          body: "Circuit breakers, sliding-window rate limits, bounded retries and idempotency keys, each with live state you can inspect instead of inferring from logs.",
          action: "Runtime status",
        },
      },
      governance: {
        authority: {
          title: "Model intelligence is not authority",
          body: "Capability never implies permission. Send, publish, delete, purchase, refund, spend, deploy and admin changes pass through policy and, where required, explicit approval.",
        },
        audited: {
          title: "Every execution is audited",
          body: "Tool runs record the tool, risk, outcome, approval requirement and the correlation ID of the request that caused them — so any action traces back to its origin.",
        },
        untrusted: {
          title: "Untrusted content stays data",
          body: "Text returned by emails, web pages, documents, connectors or MCP tools is treated as data, never as instructions. An unknown MCP tool is denied by default.",
        },
        honest: {
          title: "Honest capability states",
          body: "A connector is not \"working\" because an adapter or a card exists. Each one reports live-validated, credential-required or not-implemented — and nothing is inflated.",
        },
      },
      connectorsBody:
        "Providers are reached through a broker that prefers official MCP, then verified MCP, then a managed connector, then a native adapter. The Integrations page shows each one's real state — connected, credential required, or not implemented — rather than a count that flatters the product.",
      mcpFirst: "MCP-first, not MCP-only",
    },
    tasks: {
      title: "Tasks",
      description:
        "Create tasks and look them up by ID. The API does not expose a task list, so recent tasks from this session are tracked below.",
      lookupPlaceholder: "Paste a task ID",
      emptyTitle: "No tasks created yet",
      emptyBody: "Tasks you create above will appear here for quick lookup.",
    },
    orchestrate: {
      title: "Orchestrate",
      description:
        "Run a researcher → builder → reviewer multi-agent orchestration against a single objective.",
      objectivePlaceholder: "Design a rollout plan for the new billing system",
      contextPlaceholder: "Relevant constraints, prior decisions, or background",
      working: "Researcher, builder, and reviewer are working…",
      emptyTitle: "No orchestration run yet",
      emptyBody:
        "Enter an objective above and run it to see researcher, builder, and reviewer activity.",
    },
    autonomous: {
      title: "Autonomous Runs",
      description:
        "Planner → specialist jobs → verifier → synthesis, fully autonomous from a single objective.",
      working: "Planning, executing specialists, and verifying…",
      emptyTitle: "No autonomous run yet",
      emptyBody: "Submit an objective above to watch the planner, specialists, and verifier work.",
    },
    agents: {
      title: "Agents",
      description:
        "THYNACT runs three fixed roles per orchestration, and dynamically named specialists per autonomous run.",
    },
    workflowRuns: {
      title: "Workflow Runs",
      description:
        "Inspect a run by ID and resume it past approval pauses. The API does not expose a run list, so this session's runs are tracked below.",
      lookupPlaceholder: "Paste a workflow run ID",
      approvalIdPlaceholder: "Approval ID",
      emptyTitle: "No workflow runs yet",
      emptyBody: "Runs started from the Workflows editor appear here.",
    },
    approvals: {
      title: "Approval Center",
      description:
        "THYNACT uses single-use, pre-authorized approval grants rather than a pending-request queue.",
      emptyTitle: "No approvals issued yet",
      emptyBody: "Grants you issue above will be listed here for quick reuse in the Tools page.",
    },
    memory: {
      title: "Memory",
      description: "Search THYNACT's semantic + lexical memory, or write new memories directly.",
      searchHint: "Ranked by semantic + lexical relevance",
      listView: "List view",
      graphView: "Graph view",
      emptyTitle: "No memories found",
      emptyBody: "Try a different query or scope.",
      deleteMemory: "Delete memory",
      deleteTitle: "Delete this memory?",
      deleteBody: "This cannot be undone.",
    },
    runtime: {
      title: "Runtime",
      description:
        "Execute provider-backed workflows with retries, idempotency, and correlation tracking.",
      lookupPlaceholder: "Paste an execution ID",
      emptyTitle: "No executions triggered yet",
    },
    tools: {
      title: "Tools",
      description:
        "Browse the tool registry, issue trusted (single-use) approvals for write/high-risk tools, and execute them safely.",
      emptyTitle: "No tools registered",
      approvalPlaceholder: "Required for write/high-risk tools",
      executing: "Executing…",
    },
    integrations: {
      title: "THYNACT Integrations",
      description: "Connect intelligence to the tools that make things happen.",
      emptyTitle: "No integrations connected yet.",
      emptyBody: "Connect one below, or add an MCP server to get started.",
      searchPlaceholder: "Search integrations…",
      noMatchTitle: "No integrations match your search",
      noMatchBody: "Try a different term or clear the filters.",
      addMcpServer: "Add MCP server",
      currentlyIntegrated: "Currently integrated",
      readyToConnect: "Ready to connect",
      comingSoon: "Coming soon",
      all: "All",
      connected: "Connected",
      operatorAccessRequired:
        "Operator access required to connect, configure, or test integrations — the catalog below is still browsable.",
      actions: {
        test: "Test",
        testConnection: "Test connection",
        testFailed: "Test connection failed",
        manage: "Manage",
        learnMore: "Learn more",
        connect: "Connect {name}",
        configure: "Configure",
        configureWebhook: "Configure webhook",
        disconnect: "Disconnect",
        execute: "Execute",
      },
      detail: {
        catalogOnly:
          "Catalog only — this connector isn't built yet. It describes what THYNACT could support; no credentials are collected and no connection is possible until it's implemented.",
        requiresSetupPrefix: "Requires setup. This connector needs",
        requiresSetupSuffix: "configured on the backend before it can connect.",
        authorityTitle: "What connecting this authorises",
        authorityBody:
          "Declared capabilities. These describe the authority a connection would carry — not that every one is implemented yet.",
        canRead: "Can read",
        canChange: "Can change",
        needsApproval: "Needs your approval",
        needsApprovalBody: "THYNACT can prepare these, but cannot carry them out on its own.",
        mcpUnmapped:
          "Tools discovered from this MCP server are not mapped to canonical capabilities. An unknown tool is denied until it is mapped — a server does not get to declare its own risk level.",
        systemInfrastructure: "System infrastructure",
        systemInfrastructureBody:
          "Part of THYNACT's own running system, not an account you connect. Shown for diagnostics.",
        authType: "Auth type",
        lastCheck: "Last check",
        latency: "Latency",
        lastError: "Last error",
        lastExecution: "Last execution",
        never: "Never",
        docs: "Docs",
        capabilities: "Capabilities",
        plannedCapabilities: "Planned capabilities",
        tools: "Tools",
        resources: "Resources",
        prompts: "Prompts",
        noCapabilitiesYet: "No capabilities discovered yet — run a connection test to refresh.",
        executeWorkflow: "Execute a workflow",
        webhookWorkflow: "Webhook workflow",
        payloadJson: "Payload (JSON)",
        payloadInvalid: "Payload must be valid JSON",
        success: "Success",
        failed: "Failed",
        disconnectNamed: "Disconnect {name}?",
        disconnectMcp: "Disconnect this MCP server?",
        disconnectOAuthBody: "This forgets the stored account connection. You can reauthorize at any time.",
        disconnectMcpBody: "This removes the server configuration. This cannot be undone.",
      },
      browseTitle: "Browse connectors",
      browseBody:
        "Every entry here is a real catalog record with its live state. Protocol names (MCP, API, OAuth, webhook) are searchable.",
      allStatuses: "All",
      allCategories: "All categories",
      showingCount: "Showing {shown} of {total} connectors",
      buckets: {
        connected: {
          label: "Connected",
          hint: "Verified against the real provider.",
        },
        needs_verification: {
          label: "Needs verification",
          hint: "Credentials are set but have not been proven to work. Run a test.",
        },
        needs_setup: {
          label: "Needs setup",
          hint: "Built and ready — waiting on credentials or authorization.",
        },
        not_built: {
          label: "Not built yet",
          hint: "Catalog metadata only. There is no adapter behind these.",
        },
      },
      categories: {
        ai: "AI",
        automation: "Automation",
        productivity: "Productivity",
        google: "Google",
        developer: "Developer",
        data: "Data",
        other: "Other",
      },
    },
    audit: {
      title: "Audit Logs",
      description: "Every tool execution and approval check, most recent first.",
      filterPlaceholder: "Filter by tool…",
      tableView: "Table view",
      timelineView: "Timeline view",
      emptyTitle: "No matching audit events",
      auditEvent: "Audit event",
      copyCorrelationId: "Copy correlation ID",
    },
    health: {
      title: "System Health",
      description: "Live status straight from the backend's /health and /ready endpoints.",
      status: "Status",
      service: "Service",
      environment: "Environment",
      llmProvider: "LLM provider",
      storage: "Storage",
      overall: "Overall",
    },
    settings: {
      title: "Settings",
      description:
        "Local, frontend-only configuration. Nothing here is sent anywhere except the THYNACT API you point it at.",
      apiKeyPlaceholder: "Enter your THYNACT API key",
      apiConnection: "API connection",
      apiKeyNote:
        "The API key is kept in sessionStorage — it is cleared automatically when this tab closes and is never written to disk or logs. Prefer the server-side orchestration proxy in production; this form is for local development and trusted operator sessions.",
      apiBaseUrl: "API base URL",
      apiKeyLabel: "API key (X-API-Key)",
      clear: "Clear",
    },
    about: {
      title: "About THYNACT",
      navLabel: "About THYNACT",
      heroStatement:
        "Intelligence should do more than answer. It should move work forward — safely.",
      whyTitle: "Why THYNACT exists",
      whyBody:
        "Most AI stops at an answer. The gap between a good answer and finished work is where real systems live: credentials, permissions, side effects, and the question of who authorised what. THYNACT is built to close that gap without pretending the gap was never there.",
      thinkTitle: "Think",
      thinkBody:
        "Understand the request, route it by complexity and risk, recall what matters, plan only when planning earns its cost, and verify before acting.",
      actTitle: "Act",
      actBody:
        "Reach real services through a governed broker, execute, automate and schedule — and record every step so the result can be traced back to the request that caused it.",
      controlTitle: "Control",
      controlBody:
        "Permission, approval, identity and tenant boundaries sit around every consequential action. Capability never quietly becomes authority.",
      flowTitle: "How work moves through THYNACT",
      flowBody:
        "Consequential steps pass through control. Everything else takes the fast path.",
      flow: {
        intent: "Intent",
        think: "Think",
        plan: "Plan",
        verify: "Verify",
        act: "Act",
        result: "Result",
        control: "Control",
      },
      principlesTitle: "What it holds to",
      principles: {
        fast: {
          title: "Fast by default",
          body: "Simple work stays simple. Planning, retrieval and multi-agent execution are opt-in costs, never the default path.",
        },
        real: {
          title: "Real over mock",
          body: "\"Working\" means validated through real execution against a real provider — not that an adapter, a card or a passing mock exists.",
        },
        authority: {
          title: "Intelligence is not authority",
          body: "Sending, publishing, deleting, spending and deploying pass through policy and, where required, an approval the model cannot issue to itself.",
        },
        neutral: {
          title: "Provider neutral",
          body: "Models and tools are replaceable infrastructure. Core reasoning speaks in canonical capabilities, never a vendor's API names.",
        },
        continuity: {
          title: "Built for continuity",
          body: "Memory, workflows and durable state are designed to outlive a session, so work can be resumed rather than restarted.",
        },
        governed: {
          title: "Governed action",
          body: "Every tool run is recorded with its outcome and the correlation ID of the request behind it. An audit trail that can be quietly rewritten is not one.",
        },
      },
      visionTitle: "Where it is going",
      visionBody:
        "Stated as direction, not as shipped capability. What is live today is visible on the Product Overview and System Health pages.",
      vision: {
        surfaces: "More surfaces — mobile and voice alongside the web control centre",
        connectors: "Broader connector coverage across business systems",
        automation: "Richer scheduled and event-driven automation",
        multimodal: "Multimodal understanding where it genuinely helps the work",
      },
      ctaTitle: "Ready when you are",
      ctaBody: "Connect a service, or give THYNACT an objective and watch it work.",
      ctaPrimary: "Open the dashboard",
      ctaSecondary: "Browse connectors",
      shipped: "Available today",
      direction: "Direction",
    },
    notFound: {
      title: "Page not found",
      description: "This screen doesn't exist, or it moved.",
    },
    workflows: {
      title: "Workflows",
      description:
        "Design a step graph, then run it. There's no separate save — running a workflow persists its definition.",
      viewRuns: "View workflow runs",
      workflowName: "Workflow name",
      runContext: "Run context (JSON)",
      stepGraph: "Step graph",
      addStep: "Add step",
      deleteSelected: "Delete selected",
      runWorkflow: "Run workflow",
      started: "Workflow started",
      runFailed: "Run failed",
    },
    privacy: {
      title: "Privacy & Policy",
      description: "What THYNACT stores, where it goes, and the rules the system holds itself to.",
      lastUpdated: "Last updated {date}",
    },
  },

  status: {
    LIVE_VALIDATED: "Live validated",
    CONNECTED_NOT_VALIDATED: "Connected, not validated",
    AUTH_REQUIRED: "Authentication required",
    CREDENTIAL_REQUIRED: "Credential required",
    PROVIDER_APPROVAL_REQUIRED: "Provider approval required",
    PLATFORM_CONFIG_REQUIRED: "Platform configuration required",
    STABLE_DOMAIN_REQUIRED: "Stable domain required",
    DEGRADED: "Degraded",
    NOT_IMPLEMENTED: "Not implemented",
    UNAVAILABLE: "Unavailable",
    healthy: "Healthy",
    running: "Running",
    succeeded: "Succeeded",
    failed: "Failed",
    pending: "Pending",
    configured: "Configured",
  },

  /** StatusBadge display labels. The KEY is the machine status; only the
   * text is localized, so backend contracts are untouched. */
  badges: {
    pending: "Pending",
    running: "Running",
    completed: "Completed",
    succeeded: "Succeeded",
    failed: "Failed",
    rejected: "Rejected",
    paused: "Paused",
    skipped: "Skipped",
    waiting_approval: "Waiting approval",
    ok: "Healthy",
    healthy: "Healthy",
    unconfigured: "Unconfigured",
    unavailable: "Unavailable",
    degraded: "Degraded",
    connected: "Connected",
    configured: "Configured",
    needs_setup: "Needs setup",
    available: "Available",
    error: "Error",
    disabled: "Disabled",
  },

  counts: {
    task_one: "{count} task",
    task_other: "{count} tasks",
    event_one: "{count} event",
    event_other: "{count} events",
    result_one: "{count} result",
    result_other: "{count} results",
  },
} as const;

/**
 * Every locale must satisfy this shape.
 *
 * The mapped type replaces each literal string type from `as const` with plain
 * `string`, so the KEY STRUCTURE is enforced (a missing or misspelled key is a
 * typecheck failure) while values stay free. Using `typeof en` directly would
 * have required every other locale to repeat the English text verbatim.
 */
type Localised<T> = { [K in keyof T]: T[K] extends string ? string : Localised<T[K]> };

export type Translations = Localised<typeof en>;
