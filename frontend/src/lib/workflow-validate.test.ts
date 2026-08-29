import { describe, it, expect } from "vitest";
import { validateWorkflowGraph, invalidStepIds } from "./workflow-validate";
import type { WorkflowStep } from "./types";

function step(overrides: Partial<WorkflowStep>): WorkflowStep {
  return {
    id: "a",
    type: "noop",
    depends_on: [],
    input: {},
    max_retries: 0,
    timeout_seconds: 30,
    ...overrides,
  };
}

describe("validateWorkflowGraph", () => {
  it("accepts a valid linear graph", () => {
    const errors = validateWorkflowGraph([
      step({ id: "a" }),
      step({ id: "b", depends_on: ["a"] }),
    ]);
    expect(errors).toEqual([]);
  });

  it("requires at least one step", () => {
    expect(validateWorkflowGraph([])).toContain("Add at least one step.");
  });

  it("flags duplicate ids", () => {
    const errors = validateWorkflowGraph([step({ id: "a" }), step({ id: "a" })]);
    expect(errors.some((e) => e.includes("unique"))).toBe(true);
  });

  it("flags an unknown dependency", () => {
    const errors = validateWorkflowGraph([step({ id: "a", depends_on: ["missing"] })]);
    expect(errors.some((e) => e.includes("unknown step"))).toBe(true);
  });

  it("flags self-dependency", () => {
    const errors = validateWorkflowGraph([step({ id: "a", depends_on: ["a"] })]);
    expect(errors.some((e) => e.includes("cannot depend on itself"))).toBe(true);
  });

  it("flags a dependency cycle", () => {
    const errors = validateWorkflowGraph([
      step({ id: "a", depends_on: ["b"] }),
      step({ id: "b", depends_on: ["a"] }),
    ]);
    expect(errors.some((e) => e.includes("cycle"))).toBe(true);
  });
});

describe("invalidStepIds", () => {
  it("extracts the step id named in each error message", () => {
    const errors = validateWorkflowGraph([step({ id: "a", depends_on: ["missing"] })]);
    expect(invalidStepIds(errors)).toEqual(new Set(["a"]));
  });

  it("returns an empty set for errors that don't name a step", () => {
    expect(invalidStepIds(["Add at least one step."])).toEqual(new Set());
  });
});
