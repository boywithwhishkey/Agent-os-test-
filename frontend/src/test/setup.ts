import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// jsdom has no IntersectionObserver — framer-motion's `whileInView` (used by
// the ScrollReveal/StaggerGroup motion primitives) needs one to exist at all,
// even though it's a no-op under test.
class MockIntersectionObserver implements IntersectionObserver {
  readonly root = null;
  readonly rootMargin = "";
  readonly thresholds: ReadonlyArray<number> = [];
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}
globalThis.IntersectionObserver = MockIntersectionObserver;

afterEach(() => {
  cleanup();
  sessionStorage.clear();
  localStorage.clear();
});
