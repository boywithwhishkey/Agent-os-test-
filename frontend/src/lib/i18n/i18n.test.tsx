import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nProvider, useI18n, resolveLocale, enabledLocales, LOCALES, applyDocumentLocale } from "./index";
import { en } from "./locales/en";
import { hi } from "./locales/hi";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";

const STORAGE_KEY = "agent-os:language";

/** Every leaf path in a catalogue, e.g. "nav.items.dashboard". */
function leafPaths(node: unknown, prefix = ""): string[] {
  if (typeof node === "string") return [prefix];
  if (!node || typeof node !== "object") return [];
  return Object.entries(node as Record<string, unknown>).flatMap(([key, value]) =>
    leafPaths(value, prefix ? `${prefix}.${key}` : key)
  );
}

beforeEach(() => {
  localStorage.clear();
});

describe("locale registry", () => {
  it("offers exactly English and Hindi today", () => {
    expect(enabledLocales().map((l) => l.code).sort()).toEqual(["en", "hi"]);
  });

  it("carries direction for future RTL locales", () => {
    for (const locale of Object.values(LOCALES)) {
      expect(["ltr", "rtl"]).toContain(locale.direction);
    }
  });

  it("falls back safely for unsupported or hostile values", () => {
    expect(resolveLocale("fr")).toBe("en");
    expect(resolveLocale(null)).toBe("en");
    expect(resolveLocale("")).toBe("en");
    expect(resolveLocale("../../etc/passwd")).toBe("en");
    // Regional tags resolve to their base language.
    expect(resolveLocale("hi-IN")).toBe("hi");
    expect(resolveLocale("en-GB")).toBe("en");
  });
});

describe("translation completeness", () => {
  it("Hindi defines every key English defines", () => {
    const missing = leafPaths(en).filter((path) => !leafPaths(hi).includes(path));
    expect(missing, `Hindi is missing: ${missing.join(", ")}`).toEqual([]);
  });

  it("Hindi adds no keys English does not have", () => {
    const extra = leafPaths(hi).filter((path) => !leafPaths(en).includes(path));
    expect(extra, `Hindi has orphan keys: ${extra.join(", ")}`).toEqual([]);
  });

  it("no Hindi value is left as the English string for real copy", () => {
    // Product nouns like "API" legitimately stay in English; navigation and
    // dashboard copy must not.
    const untranslated = Object.entries(en.nav.items).filter(
      ([key, value]) => hi.nav.items[key as keyof typeof hi.nav.items] === value
    );
    expect(untranslated.map(([k]) => k)).toEqual([]);
  });

  it("keeps every placeholder that English declares", () => {
    const placeholders = (s: string) => (s.match(/\{(\w+)\}/g) ?? []).sort();
    for (const path of leafPaths(en)) {
      const read = (o: unknown) =>
        path.split(".").reduce<never>((n, p) => (n as never)?.[p as never], o as never) as unknown;
      const enValue = read(en) as string;
      const hiValue = read(hi) as string;
      if (typeof enValue !== "string" || typeof hiValue !== "string") continue;
      expect(placeholders(hiValue), `placeholder mismatch at ${path}`).toEqual(placeholders(enValue));
    }
  });
});

function Probe() {
  const { t, locale, plural, setLocale, formatNumber } = useI18n();
  return (
    <div>
      <span data-testid="locale">{locale}</span>
      <span data-testid="nav">{t("nav.items.dashboard")}</span>
      <span data-testid="status">{t("status.AUTH_REQUIRED")}</span>
      <span data-testid="interp">{t("language.switchTo", { language: "X" })}</span>
      <span data-testid="one">{plural("counts.event", 1)}</span>
      <span data-testid="many">{plural("counts.event", 5)}</span>
      <span data-testid="num">{formatNumber(1234567)}</span>
      <button onClick={() => setLocale("hi")}>go-hi</button>
    </div>
  );
}

describe("translation behaviour", () => {
  it("renders English by default and Hindi after switching", async () => {
    const user = userEvent.setup();
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>
    );
    expect(screen.getByTestId("nav")).toHaveTextContent("Dashboard");
    expect(screen.getByTestId("status")).toHaveTextContent("Authentication required");

    await user.click(screen.getByText("go-hi"));

    expect(screen.getByTestId("locale")).toHaveTextContent("hi");
    expect(screen.getByTestId("nav")).toHaveTextContent("डैशबोर्ड");
    expect(screen.getByTestId("status")).toHaveTextContent("प्रमाणीकरण आवश्यक");
  });

  it("interpolates instead of concatenating", () => {
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>
    );
    expect(screen.getByTestId("interp")).toHaveTextContent("Switch to X");
  });

  it("pluralises per locale, not by an English rule", async () => {
    const user = userEvent.setup();
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>
    );
    expect(screen.getByTestId("one")).toHaveTextContent("1 event");
    expect(screen.getByTestId("many")).toHaveTextContent("5 events");

    await user.click(screen.getByText("go-hi"));

    // Hindi inflects this noun: घटना -> घटनाएँ.
    expect(screen.getByTestId("one")).toHaveTextContent("1 घटना");
    expect(screen.getByTestId("many")).toHaveTextContent("5 घटनाएँ");
  });

  it("persists the choice and restores it on remount", async () => {
    const user = userEvent.setup();
    const { unmount } = render(
      <I18nProvider>
        <Probe />
      </I18nProvider>
    );
    await user.click(screen.getByText("go-hi"));
    expect(localStorage.getItem(STORAGE_KEY)).toBe("hi");
    unmount();

    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>
    );
    expect(screen.getByTestId("locale")).toHaveTextContent("hi");
    expect(screen.getByTestId("nav")).toHaveTextContent("डैशबोर्ड");
  });

  it("ignores an unsupported stored value rather than breaking", () => {
    localStorage.setItem(STORAGE_KEY, "klingon");
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>
    );
    expect(screen.getByTestId("locale")).toHaveTextContent("en");
  });

  it("survives localStorage throwing", () => {
    const spy = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>
    );
    // The switch must still apply even though it cannot be saved.
    act(() => {
      screen.getByText("go-hi").click();
    });
    expect(screen.getByTestId("locale")).toHaveTextContent("hi");
    spy.mockRestore();
  });
});

describe("document locale attributes", () => {
  it("updates html lang and dir when the language changes", async () => {
    const user = userEvent.setup();
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>
    );
    expect(document.documentElement.getAttribute("lang")).toBe("en");
    expect(document.documentElement.getAttribute("dir")).toBe("ltr");

    await user.click(screen.getByText("go-hi"));

    expect(document.documentElement.getAttribute("lang")).toBe("hi");
    expect(document.documentElement.getAttribute("dir")).toBe("ltr");
  });
});

describe("LanguageSwitcher", () => {
  it("renders every enabled locale from the registry", () => {
    render(
      <I18nProvider>
        <LanguageSwitcher />
      </I18nProvider>
    );
    expect(screen.getAllByRole("radio")).toHaveLength(enabledLocales().length);
  });

  it("marks the active language and switches on click", async () => {
    const user = userEvent.setup();
    render(
      <I18nProvider>
        <>
          <LanguageSwitcher />
          <Probe />
        </>
      </I18nProvider>
    );
    const hindi = screen.getByRole("radio", { name: /हिंदी/ });
    expect(hindi).toHaveAttribute("aria-checked", "false");

    await user.click(hindi);

    expect(screen.getByTestId("nav")).toHaveTextContent("डैशबोर्ड");
    expect(screen.getByRole("radio", { name: /हिंदी/ })).toHaveAttribute("aria-checked", "true");
  });

  it("is a labelled radiogroup for assistive technology", () => {
    render(
      <I18nProvider>
        <LanguageSwitcher />
      </I18nProvider>
    );
    expect(screen.getByRole("radiogroup")).toHaveAccessibleName();
  });

  it("switches with the keyboard", async () => {
    const user = userEvent.setup();
    render(
      <I18nProvider>
        <>
          <LanguageSwitcher />
          <Probe />
        </>
      </I18nProvider>
    );
    const active = screen.getByRole("radio", { name: /English/ });
    active.focus();
    await user.keyboard("{ArrowRight}");

    expect(screen.getByTestId("nav")).toHaveTextContent("डैशबोर्ड");
  });

  it("does not disturb the stored theme preference", async () => {
    const user = userEvent.setup();
    localStorage.setItem("agent-os:theme", "light");
    render(
      <I18nProvider>
        <LanguageSwitcher />
      </I18nProvider>
    );
    await user.click(screen.getByRole("radio", { name: /हिंदी/ }));

    expect(localStorage.getItem("agent-os:theme")).toBe("light");
    expect(localStorage.getItem(STORAGE_KEY)).toBe("hi");
  });
});


describe("future-language extensibility", () => {
  /**
   * The point of the registry is that a third language needs no component
   * change. This proves the switcher renders whatever the registry declares
   * rather than being hardcoded to two branches — WITHOUT enabling a third
   * production locale, by mutating the registry object for the duration of the
   * test only.
   */
  it("renders a newly registered locale without touching the component", () => {
    const before = screen.queryAllByRole("radio").length;
    expect(before).toBe(0);

    // A hypothetical Spanish entry, registered the way a real one would be.
    (LOCALES as Record<string, (typeof LOCALES)["en"]>).es = {
      code: "es",
      label: "Spanish",
      nativeLabel: "Español",
      shortLabel: "ES",
      direction: "ltr",
      intlLocale: "es",
      enabled: true,
    };
    try {
      render(
        <I18nProvider>
          <LanguageSwitcher />
        </I18nProvider>
      );
      expect(screen.getAllByRole("radio")).toHaveLength(3);
      expect(screen.getByRole("radio", { name: /Español/ })).toBeInTheDocument();
    } finally {
      delete (LOCALES as Record<string, unknown>).es;
    }
  });

  it("hides a registered but disabled locale from users", () => {
    (LOCALES as Record<string, (typeof LOCALES)["en"]>).pt = {
      code: "pt",
      label: "Portuguese",
      nativeLabel: "Português",
      shortLabel: "PT",
      direction: "ltr",
      intlLocale: "pt",
      // Translations still in progress — must never reach the UI.
      enabled: false,
    };
    try {
      render(
        <I18nProvider>
          <LanguageSwitcher />
        </I18nProvider>
      );
      expect(screen.queryByRole("radio", { name: /Português/ })).not.toBeInTheDocument();
      expect(screen.getAllByRole("radio")).toHaveLength(2);
    } finally {
      delete (LOCALES as Record<string, unknown>).pt;
    }
  });

  it("applies dir=rtl for a future right-to-left locale", () => {
    // English and Hindi are both LTR, so nothing else exercises this. It proves
    // the document plumbing reads direction from the registry rather than
    // assuming LTR everywhere.
    (LOCALES as Record<string, (typeof LOCALES)["en"]>).ar = {
      code: "ar",
      label: "Arabic",
      nativeLabel: "العربية",
      shortLabel: "AR",
      direction: "rtl",
      intlLocale: "ar",
      enabled: true,
    };
    try {
      applyDocumentLocale("ar");
      expect(document.documentElement.getAttribute("dir")).toBe("rtl");
      expect(document.documentElement.getAttribute("lang")).toBe("ar");
    } finally {
      delete (LOCALES as Record<string, unknown>).ar;
      applyDocumentLocale("en");
    }
  });
});

describe("page copy is translated, not just navigation", () => {
  it.each([
    ["pages.settings.title", "सेटिंग्स"],
    ["pages.integrations.searchPlaceholder", "इंटीग्रेशन खोजें…"],
    ["pages.audit.tableView", "तालिका दृश्य"],
    ["pages.memory.deleteTitle", "यह मेमोरी हटाएँ?"],
    ["pages.tools.executing", "चल रहा है…"],
  ])("%s is Hindi", (key, expected) => {
    const read = (o: unknown) =>
      key.split(".").reduce<never>((n, p) => (n as never)?.[p as never], o as never) as unknown;
    expect(read(hi)).toBe(expected);
  });
});
