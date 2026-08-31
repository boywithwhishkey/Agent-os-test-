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

export interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
}
export interface NavGroup {
  label: string;
  items: NavItem[];
}

export const navGroups: NavGroup[] = [
  {
    label: "Overview",
    items: [
      { label: "Dashboard", to: "/", icon: LayoutDashboard },
      { label: "Product Overview", to: "/overview", icon: Sparkles },
    ],
  },
  {
    label: "Execution",
    items: [
      { label: "Tasks", to: "/tasks", icon: ListTodo },
      { label: "Orchestrate", to: "/orchestrate", icon: Workflow },
      { label: "Autonomous Runs", to: "/autonomous", icon: Bot },
      { label: "Agents", to: "/agents", icon: Users },
    ],
  },
  {
    label: "Workflows",
    items: [
      { label: "Workflows", to: "/workflows", icon: GitBranch },
      { label: "Workflow Runs", to: "/workflows/runs", icon: History },
      { label: "Approvals", to: "/approvals", icon: ShieldCheck },
    ],
  },
  {
    label: "Knowledge",
    items: [{ label: "Memory", to: "/memory", icon: Brain }],
  },
  {
    label: "Operations",
    items: [
      { label: "Runtime", to: "/runtime", icon: Server },
      { label: "Tools", to: "/tools", icon: Wrench },
      { label: "Integrations", to: "/integrations", icon: Plug },
      { label: "Audit Logs", to: "/audit", icon: ScrollText },
    ],
  },
  {
    label: "System",
    items: [
      { label: "Health", to: "/system-health", icon: HeartPulse },
      { label: "Settings", to: "/settings", icon: Settings },
      { label: "Privacy & Policy", to: "/privacy", icon: FileLock2 },
    ],
  },
];

export const allNavItems: NavItem[] = navGroups.flatMap((g) => g.items);
