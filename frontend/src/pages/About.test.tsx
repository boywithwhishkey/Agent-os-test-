import { describe, it, expect, afterEach } from "vitest";
import { screen, cleanup } from "@testing-library/react";
import { renderWithProviders } from "@/test/utils";
import About from "./About";
import { en } from "@/lib/i18n/locales/en";
import { hi } from "@/lib/i18n/locales/hi";

describe("About page", () => {
  afterEach(cleanup);

  // "Think", "Act" and "Control" each appear twice on this page — once as a
  // narrative card and once as a step in the chain. Resolve to the chain node.
  const node = (label: string): HTMLElement => {
    const el = screen.getAllByText(label).find((e) => e.tagName === "LI");
    expect(el, `no flow node labelled ${label}`).toBeDefined();
    return el as HTMLElement;
  };

  it("renders the full reasoning chain with the governed steps inside CONTROL", () => {
    renderWithProviders(<About />);

    const flow = en.pages.about.flow;
    for (const step of [flow.intent, flow.think, flow.plan, flow.verify, flow.act, flow.result]) {
      expect(node(step)).toBeInTheDocument();
    }

    // CONTROL must ENCLOSE plan/verify/act — a diagram that merely prints the
    // label somewhere on the page would satisfy a naive text assertion while
    // showing governance as an unrelated aside.
    const control = screen.getAllByText(flow.control).find((e) => e.tagName === "SPAN")?.parentElement;
    expect(control).toBeTruthy();
    for (const step of [flow.plan, flow.verify, flow.act]) {
      expect(control!).toContainElement(node(step));
    }
    for (const step of [flow.intent, flow.think, flow.result]) {
      expect(control!).not.toContainElement(node(step));
    }
  });

  it("separates shipped capability from stated direction", () => {
    renderWithProviders(<About />);
    // The forward-looking section must carry the "direction" badge, so nothing
    // on this page can read as available when it isn't.
    expect(screen.getByText(en.pages.about.shipped)).toBeInTheDocument();
    expect(screen.getByText(en.pages.about.direction)).toBeInTheDocument();
  });

  it("carries no untranslated copy — every About string exists in Hindi too", () => {
    // Guards the failure mode this page is most prone to: brand-voice prose
    // added straight into the JSX and never given a Hindi counterpart.
    const walk = (a: unknown, b: unknown, path: string): void => {
      if (typeof a === "string") {
        expect(typeof b, `missing Hindi value at ${path}`).toBe("string");
        return;
      }
      for (const key of Object.keys(a as object)) {
        walk((a as Record<string, unknown>)[key], (b as Record<string, unknown>)?.[key], `${path}.${key}`);
      }
    };
    walk(en.pages.about, hi.pages.about, "pages.about");
  });
});
