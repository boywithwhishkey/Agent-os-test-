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
    tasks: { title: "Tasks" },
    orchestrate: { title: "Orchestrate" },
    autonomous: { title: "Autonomous Runs" },
    agents: { title: "Agents" },
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
    workflowRuns: { title: "Workflow Runs" },
    approvals: { title: "Approvals" },
    memory: { title: "Memory" },
    runtime: { title: "Runtime" },
    tools: { title: "Tools" },
    integrations: { title: "Integrations" },
    audit: { title: "Audit Logs" },
    health: { title: "System Health" },
    settings: { title: "Settings" },
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
