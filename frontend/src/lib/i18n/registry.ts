/**
 * The single source of truth for which languages exist and how they behave.
 *
 * Adding a language is: add a `Locale` entry here, add its translation file,
 * run the completeness test. No component learns about the new language —
 * everything that renders a language list reads this registry, so nothing
 * anywhere is allowed to contain `if (lang === "hi")`.
 *
 * `direction` is carried from day one even though English and Hindi are both
 * LTR. It costs nothing now and means a future RTL locale is a registry entry
 * plus translations, not a rewrite of the document-attribute plumbing.
 */
export interface LocaleDefinition {
  /** BCP 47 code. Also the value written to <html lang>. */
  code: string;
  /** English name, for developer-facing surfaces and docs. */
  label: string;
  /** The language's own name — what a speaker of it expects to see. */
  nativeLabel: string;
  /** Compact form for the switcher, where a full native name will not fit. */
  shortLabel: string;
  direction: "ltr" | "rtl";
  /** Passed to Intl for dates, numbers and plural rules. */
  intlLocale: string;
  /**
   * Only enabled locales are offered to users. A locale can sit here
   * fully-formed while its translations are still being written, without ever
   * appearing half-finished in the product.
   */
  enabled: boolean;
}

export const LOCALES: Record<string, LocaleDefinition> = {
  en: {
    code: "en",
    label: "English",
    nativeLabel: "English",
    shortLabel: "EN",
    direction: "ltr",
    intlLocale: "en",
    enabled: true,
  },
  hi: {
    code: "hi",
    label: "Hindi",
    nativeLabel: "हिंदी",
    shortLabel: "हिंदी",
    direction: "ltr",
    intlLocale: "hi-IN",
    enabled: true,
  },
};

export const FALLBACK_LOCALE = "en";

export type LocaleCode = keyof typeof LOCALES;

/** The languages the UI may offer. Order is the order they render in. */
export function enabledLocales(): LocaleDefinition[] {
  return Object.values(LOCALES).filter((locale) => locale.enabled);
}

export function isSupportedLocale(code: string | null | undefined): boolean {
  return Boolean(code && LOCALES[code]?.enabled);
}

/**
 * Resolve any candidate — a stored preference, a browser tag like "hi-IN", a
 * hostile query string — down to a locale we actually ship. Never throws and
 * never returns something unsupported, so an unexpected browser language can't
 * break the app.
 */
export function resolveLocale(candidate: string | null | undefined): string {
  if (!candidate) return FALLBACK_LOCALE;
  const normalized = candidate.trim().toLowerCase();
  if (isSupportedLocale(normalized)) return normalized;
  // "hi-IN" / "en-GB" -> match on the primary subtag.
  const base = normalized.split("-")[0];
  if (isSupportedLocale(base)) return base;
  return FALLBACK_LOCALE;
}

export function getLocale(code: string): LocaleDefinition {
  return LOCALES[code] ?? LOCALES[FALLBACK_LOCALE];
}
