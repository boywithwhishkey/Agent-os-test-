import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MotionConfig } from "framer-motion";
import { ThemeProvider } from "@/lib/theme";
import { ToastProvider } from "@/components/ui/Toast";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { AppShell } from "@/components/layout/AppShell";
import { LoadingState } from "@/components/ui/States";

const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Tasks = lazy(() => import("@/pages/Tasks"));
const Orchestrate = lazy(() => import("@/pages/Orchestrate"));
const Autonomous = lazy(() => import("@/pages/Autonomous"));
const Agents = lazy(() => import("@/pages/Agents"));
const Workflows = lazy(() => import("@/pages/Workflows"));
const WorkflowRuns = lazy(() => import("@/pages/WorkflowRuns"));
const Approvals = lazy(() => import("@/pages/Approvals"));
const Memory = lazy(() => import("@/pages/Memory"));
const Runtime = lazy(() => import("@/pages/Runtime"));
const Tools = lazy(() => import("@/pages/Tools"));
const Integrations = lazy(() => import("@/pages/Integrations"));
const Audit = lazy(() => import("@/pages/Audit"));
const SystemHealth = lazy(() => import("@/pages/SystemHealth"));
const Settings = lazy(() => import("@/pages/Settings"));
const NotFound = lazy(() => import("@/pages/NotFound"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 10_000,
    },
  },
});

export function App() {
  return (
    <ErrorBoundary>
      <MotionConfig reducedMotion="user">
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <ToastProvider>
            <BrowserRouter>
              <a
                href="#main-content"
                className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-accent-violet focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white"
              >
                Skip to content
              </a>
              <Suspense fallback={<LoadingState label="Loading Agent OS…" />}>
                <Routes>
                  <Route element={<AppShell />}>
                    <Route index element={<Dashboard />} />
                    <Route path="tasks" element={<Tasks />} />
                    <Route path="orchestrate" element={<Orchestrate />} />
                    <Route path="autonomous" element={<Autonomous />} />
                    <Route path="agents" element={<Agents />} />
                    <Route path="workflows" element={<Workflows />} />
                    <Route path="workflows/runs" element={<WorkflowRuns />} />
                    <Route path="approvals" element={<Approvals />} />
                    <Route path="memory" element={<Memory />} />
                    <Route path="runtime" element={<Runtime />} />
                    <Route path="tools" element={<Tools />} />
                    <Route path="integrations" element={<Integrations />} />
                    <Route path="audit" element={<Audit />} />
                    <Route path="system-health" element={<SystemHealth />} />
                    <Route path="settings" element={<Settings />} />
                    <Route path="*" element={<NotFound />} />
                  </Route>
                </Routes>
              </Suspense>
            </BrowserRouter>
          </ToastProvider>
        </QueryClientProvider>
      </ThemeProvider>
      </MotionConfig>
    </ErrorBoundary>
  );
}
