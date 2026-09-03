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
  },

  pages: {
    overview: {
      title: "Product Overview",
      heroTitle: "An agent platform that thinks first, then acts under your control.",
      whatItDoes: "What it does",
      everyItemLinks: "Every item links to the live surface",
      howItStaysTrustworthy: "How it stays trustworthy",
      trustworthyBody:
        "Autonomy is only useful if it is bounded. These are enforced in code, not described in a policy document.",
      startOrchestration: "Start an orchestration",
      browseConnectors: "Browse connectors",
      connectors: "Connectors",
      viewIntegrations: "View integrations",
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
