import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  ListTodo,
  Workflow,
  Bot,
  Users,
  GitBranch,
  History,
  ShieldCheck,
  Brain,
  Server,
  Wrench,
  Plug,
  ScrollText,
  HeartPulse,
  Settings,
  Sparkles,
  FileLock2,
} from "lucide-react";

/**
 * Navigation is defined by translation KEYS, never by display strings. Routes
 * (`to`) are internal identifiers and are deliberately not translated — a
 * localised UI must not change its URLs.
 */
export interface NavItem {
  /** Translation key, e.g. "nav.items.dashboard". */
  labelKey: string;
  to: string;
  icon: LucideIcon;
}
export interface NavGroup {
  /** Translation key, e.g. "nav.groups.overview". */
  labelKey: string;
  items: NavItem[];
}

export const navGroups: NavGroup[] = [
  {
    labelKey: "nav.groups.overview",
    items: [
      { labelKey: "nav.items.dashboard", to: "/", icon: LayoutDashboard },
      { labelKey: "nav.items.productOverview", to: "/overview", icon: Sparkles },
    ],
  },
  {
    labelKey: "nav.groups.execution",
    items: [
      { labelKey: "nav.items.tasks", to: "/tasks", icon: ListTodo },
      { labelKey: "nav.items.orchestrate", to: "/orchestrate", icon: Workflow },
      { labelKey: "nav.items.autonomousRuns", to: "/autonomous", icon: Bot },
      { labelKey: "nav.items.agents", to: "/agents", icon: Users },
    ],
  },
  {
    labelKey: "nav.groups.workflows",
    items: [
      { labelKey: "nav.items.workflows", to: "/workflows", icon: GitBranch },
      { labelKey: "nav.items.workflowRuns", to: "/workflows/runs", icon: History },
      { labelKey: "nav.items.approvals", to: "/approvals", icon: ShieldCheck },
    ],
  },
  {
    labelKey: "nav.groups.knowledge",
    items: [{ labelKey: "nav.items.memory", to: "/memory", icon: Brain }],
  },
  {
    labelKey: "nav.groups.operations",
    items: [
      { labelKey: "nav.items.runtime", to: "/runtime", icon: Server },
      { labelKey: "nav.items.tools", to: "/tools", icon: Wrench },
      { labelKey: "nav.items.integrations", to: "/integrations", icon: Plug },
      { labelKey: "nav.items.auditLogs", to: "/audit", icon: ScrollText },
    ],
  },
  {
    labelKey: "nav.groups.system",
    items: [
      { labelKey: "nav.items.health", to: "/system-health", icon: HeartPulse },
      { labelKey: "nav.items.settings", to: "/settings", icon: Settings },
      { labelKey: "nav.items.privacy", to: "/privacy", icon: FileLock2 },
    ],
  },
];

export const allNavItems: NavItem[] = navGroups.flatMap((g) => g.items);
