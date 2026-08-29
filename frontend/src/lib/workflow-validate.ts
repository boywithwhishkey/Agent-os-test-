import type { WorkflowStep } from "./types";

// Mirrors the validation in app/workflows/models.py WorkflowDefinition.validate_graph
// so the editor can give instant feedback before hitting the API.
export function validateWorkflowGraph(steps: WorkflowStep[]): string[] {
  const errors: string[] = [];
  const ids = steps.map((s) => s.id);
  const idSet = new Set(ids);

  if (steps.length === 0) errors.push("Add at least one step.");
  if (ids.length !== idSet.size) errors.push("Step ids must be unique.");

  for (const step of steps) {
    const missing = step.depends_on.filter((dep) => !idSet.has(dep));
    if (missing.length) errors.push(`Step "${step.id}" depends on unknown step(s): ${missing.join(", ")}`);
    if (step.depends_on.includes(step.id)) errors.push(`Step "${step.id}" cannot depend on itself.`);
  }

  const deps = new Map(steps.map((s) => [s.id, s.depends_on]));
  const visiting = new Set<string>();
  const visited = new Set<string>();
  let cycle = false;
  const visit = (node: string) => {
    if (visiting.has(node)) {
      cycle = true;
      return;
    }
    if (visited.has(node)) return;
    visiting.add(node);
    for (const dep of deps.get(node) ?? []) visit(dep);
    visiting.delete(node);
    visited.add(node);
  };
  for (const id of ids) visit(id);
  if (cycle) errors.push("The workflow contains a dependency cycle.");

  return errors;
}

// Every message above that names a step wraps its id in double quotes
// (`Step "x" ...`), so this stays in sync with validateWorkflowGraph without
// needing a structured error type that would ripple through its API/tests.
export function invalidStepIds(errors: string[]): Set<string> {
  const ids = new Set<string>();
  for (const error of errors) {
    const match = error.match(/Step "([^"]+)"/);
    if (match) ids.add(match[1]);
  }
  return ids;
}
