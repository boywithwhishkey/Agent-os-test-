import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { FALLBACK_LOCALE, getLocale, resolveLocale, type LocaleDefinition } from "./registry";
import { en, type Translations } from "./locales/en";
import { hi } from "./locales/hi";

/**
 * A small typed i18n layer, deliberately not react-i18next.
 *
 * The app already has a proven Context + localStorage preference pattern
 * (ThemeProvider), is client-only Vite, and ships two locales. i18next plus
 * react-i18next would add roughly 40 kB gzipped and a second state-management
 * layer to do what ~120 lines do here — and it would make keys plain strings,
 * where this catalogue is typed, so a missing key is a build failure instead of
 * a raw key shown to a user. If the catalogue ever grows past a few locales,
 * `CATALOGUES` is the one place a dynamic import would go.
 */
const CATALOGUES: Record<string, Translations> = { en, hi };

const STORAGE_KEY = "agent-os:language";

/** Dotted paths into the catalogue, e.g. "nav.items.dashboard". */
type Join<K, P> = K extends string ? (P extends string ? `${K}.${P}` : K) : never;
type Paths<T> = T extends object
  ? { [K in keyof T]-?: K extends string ? (T[K] extends string ? K : Join<K, Paths<T[K]>>) : never }[keyof T]
  : never;
export type TranslationKey = Paths<Translations>;

interface I18nContextValue {
  locale: string;
  definition: LocaleDefinition;
  setLocale: (code: string) => void;
  t: (key: TranslationKey, vars?: Record<string, string | number>) => string;
  /** Plural-aware lookup: picks `<key>_one` / `<key>_other` via CLDR rules. */
  plural: (key: string, count: number, vars?: Record<string, string | number>) => string;
  formatNumber: (value: number) => string;
  formatDate: (value: Date | string | number, options?: Intl.DateTimeFormatOptions) => string;
}

function buildValue(locale: string, setLocale: (code: string) => void): I18nContextValue {
  const definition = getLocale(locale);
  const catalogue = CATALOGUES[locale] ?? en;

  const t = (key: TranslationKey, vars?: Record<string, string | number>) => {
    // English is the fallback for a key this locale has not translated yet,
    // so a gap degrades to a real English sentence rather than "nav.items.x".
    const template = lookup(catalogue, key) ?? lookup(en, key);
    if (template === undefined) {
      if (import.meta.env.DEV) console.warn(`[i18n] missing key: ${key}`);
      return key;
    }
    return interpolate(template, vars);
  };

  const plural = (key: string, count: number, vars?: Record<string, string | number>) => {
    // Real CLDR categories per locale — English pluralises "task", Hindi does
    // not, and Hindi DOES pluralise "घटना". One English-shaped rule applied to
    // every language would get both wrong.
    const category = new Intl.PluralRules(definition.intlLocale).select(count);
    const template =
      lookup(catalogue, `${key}_${category}`) ??
      lookup(catalogue, `${key}_other`) ??
      lookup(en, `${key}_${category}`) ??
      lookup(en, `${key}_other`);
    if (template === undefined) return key;
    return interpolate(template, { count, ...vars });
  };

  return {
    locale,
    definition,
    setLocale,
    t,
    plural,
    formatNumber: (v: number) => new Intl.NumberFormat(definition.intlLocale).format(v),
    formatDate: (v, options) =>
      new Intl.DateTimeFormat(definition.intlLocale, options).format(new Date(v)),
  };
}

/**
 * The default is a WORKING English context, not null.
 *
 * A leaf component rendered outside the provider then falls back to English —
 * which is the specified fallback language anyway — instead of throwing and
 * taking out the whole tree. The app mounts I18nProvider at the root and a
 * test asserts that switching works there, so this degrades gracefully without
 * hiding a broken wire-up.
 */
const I18nContext = createContext<I18nContextValue>(
  buildValue(FALLBACK_LOCALE, () => {})
);

function lookup(catalogue: unknown, key: string): string | undefined {
  const value = key.split(".").reduce<unknown>(
    (node, part) => (node && typeof node === "object" ? (node as Record<string, unknown>)[part] : undefined),
    catalogue
  );
  return typeof value === "string" ? value : undefined;
}

/** Replaces {name} placeholders. Never concatenate — word order varies. */
function interpolate(template: string, vars?: Record<string, string | number>): string {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (match, name) =>
    name in vars ? String(vars[name]) : match
  );
}

/**
 * Precedence: explicit saved choice → browser language → English. Anything
 * unsupported resolves to English rather than throwing, so a browser set to a
 * language we do not ship can never break the app.
 */
export function detectInitialLocale(): string {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return resolveLocale(stored);
  } catch {
    /* storage unavailable (private mode, blocked cookies) — fall through */
  }
  if (typeof navigator !== "undefined") {
    for (const candidate of navigator.languages ?? [navigator.language]) {
      const resolved = resolveLocale(candidate);
      if (resolved !== FALLBACK_LOCALE) return resolved;
    }
  }
  return FALLBACK_LOCALE;
}

/** Keeps <html lang> and dir truthful for screen readers and future RTL. */
export function applyDocumentLocale(code: string): void {
  const definition = getLocale(code);
  const root = document.documentElement;
  root.setAttribute("lang", definition.code);
  root.setAttribute("dir", definition.direction);
}

export function I18nProvider({ children }: { children: ReactNode }) {
  // Resolved during the first render, not in an effect: reading the preference
  // afterwards would paint English first and then swap, which is the language
  // flash this is specifically meant to avoid.
  const [locale, setLocaleState] = useState<string>(() => detectInitialLocale());

  useEffect(() => {
    applyDocumentLocale(locale);
  }, [locale]);

  const setLocale = useCallback((code: string) => {
    const resolved = resolveLocale(code);
    setLocaleState(resolved);
    try {
      localStorage.setItem(STORAGE_KEY, resolved);
    } catch {
      // A failed write must not prevent the switch — the user still gets the
      // language they asked for, it just won't survive a reload.
    }
  }, []);

  const value = useMemo(() => buildValue(locale, setLocale), [locale, setLocale]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}

/** Convenience for the common case of only needing the lookup function. */
export function useT() {
  return useI18n().t;
}

export { LOCALES, enabledLocales, resolveLocale, getLocale, FALLBACK_LOCALE } from "./registry";
export type { LocaleDefinition } from "./registry";
