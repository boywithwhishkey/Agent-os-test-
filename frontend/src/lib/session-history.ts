// The backend does not expose "list all" endpoints for tasks, workflow runs,
// or runtime executions (only create + get-by-id). To avoid losing IDs the
// user just created, we keep a small session-local index of *real* API
// responses. This is explicitly labeled "this session" in the UI — it is
// never presented as authoritative backend data.
import { useSyncExternalStore } from "react";

export interface HistoryEntry {
  id: string;
  label: string;
  createdAt: string;
}

type HistoryKind = "task" | "workflow-run" | "runtime-execution" | "approval";

const STORE_KEY = "agent-os:session-history";
const listeners = new Set<() => void>();

type Store = Record<HistoryKind, HistoryEntry[]>;

function load(): Store {
  try {
    const raw = sessionStorage.getItem(STORE_KEY);
    if (raw) return JSON.parse(raw) as Store;
  } catch {
    /* ignore */
  }
  return { task: [], "workflow-run": [], "runtime-execution": [], approval: [] };
}

let store = load();

function persist() {
  try {
    sessionStorage.setItem(STORE_KEY, JSON.stringify(store));
  } catch {
    /* ignore */
  }
  listeners.forEach((listener) => listener());
}

export function recordHistory(kind: HistoryKind, entry: HistoryEntry) {
  store = {
    ...store,
    [kind]: [entry, ...store[kind].filter((e) => e.id !== entry.id)].slice(0, 25),
  };
  persist();
}

export function clearHistory(kind: HistoryKind) {
  store = { ...store, [kind]: [] };
  persist();
}

export function useSessionHistory(kind: HistoryKind): HistoryEntry[] {
  return useSyncExternalStore(
    (onChange) => {
      listeners.add(onChange);
      return () => listeners.delete(onChange);
    },
    () => store[kind]
  );
}
