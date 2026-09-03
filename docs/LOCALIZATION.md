# Localization

THYNACT ships **English (`en`)** and **Hindi (`hi`)**. English is the fallback.

## Architecture

No i18n library. The app already had a proven Context + `localStorage`
preference pattern (`ThemeProvider`), is client-only Vite, and ships two
locales — `i18next` + `react-i18next` would have added ~40 kB gzipped and a
second state layer to do what `src/lib/i18n/` does in ~120 lines. The whole
system costs **+6.45 kB gzipped**, both locales included.

The catalogue is TypeScript, not JSON, so keys are checked at compile time. A
missing or misspelled key in any locale is a build failure rather than a raw
key shown to a user — which string-keyed libraries cannot give you.

```
src/lib/i18n/
  registry.ts        which languages exist and how they behave
  index.tsx          provider, useI18n/useT, interpolation, plurals, Intl
  locales/en.ts      canonical catalogue — defines the SHAPE
  locales/hi.ts      typed as Translations, so gaps fail typecheck
  i18n.test.tsx      behaviour + completeness safeguards
```

## Adding a language

Roughly four steps, and **no component changes**:

1. `src/lib/i18n/locales/es.ts` — copy `en.ts`, translate the values, type it
   `Translations`.
2. Register it in `CATALOGUES` in `index.tsx`.
3. Add a `LOCALES` entry in `registry.ts` (`direction`, `intlLocale`,
   `nativeLabel`, `shortLabel`).
4. `enabled: true` once translations are complete.

The `LanguageSwitcher` renders `enabledLocales()`, so the new language appears
by itself. Nothing anywhere branches on a specific language code — a
`lang === "hi" ? … : …` anywhere is a bug.

Keep `enabled: false` while a translation is in progress: the locale can sit
fully wired in the repo without ever appearing half-finished to users.

## Naming

`domain.thing`, e.g. `nav.items.dashboard`, `dashboard.quickActions`,
`states.authRequiredTitle`. Add the key to `en.ts` first — it defines the shape
everything else must satisfy.

## Dynamic values

Interpolate; never concatenate. Word order differs between languages, so
`"Found " + n + " tasks"` cannot be translated correctly.

```ts
t("language.switchTo", { language: "हिंदी" })   // "{language} पर स्विच करें"
plural("counts.event", 5)                       // "5 घटनाएँ"
```

Plurals use `Intl.PluralRules` with the locale's real CLDR categories. English
pluralises "task"; Hindi does not — but Hindi *does* pluralise घटना → घटनाएँ.
One English-shaped rule applied everywhere gets both wrong.

Dates and numbers go through `formatDate` / `formatNumber`, which use the
locale's `intlLocale`.

## What must NOT be translated

- User-generated content: task text, workflow names, usernames, repo names
- Provider responses, logs, audit payload values, IDs, filenames
- **API machine codes** — `LIVE_VALIDATED`, `AUTH_REQUIRED`, `DEGRADED`,
  `auth_not_configured`. The code is the contract; only its *display label* is
  translated, via `status.*` and `errorCodes.*`.
- Route paths. A localised UI keeps stable URLs.
- The brand wordmark and tagline.

When the API returns prose, prefer localising by its `code` field over
translating the sentence it sent.

## Fallback

Explicit saved choice → browser language → English. Anything unsupported
resolves to English rather than throwing, so a browser set to a language we do
not ship cannot break the app. A key missing from a locale falls back to the
English string, not to a raw key.

The context default is a working English instance, so a component rendered
outside `I18nProvider` degrades to English instead of crashing.

## RTL readiness

`direction` is carried in the registry from day one and written to
`<html dir>`. English and Hindi are both LTR, so nothing exercises it yet, but
adding an RTL locale is a registry entry plus translations — not a rewrite.
Prefer logical CSS properties in new work.

## Testing

`pnpm test src/lib/i18n` covers registry behaviour, switching, persistence,
`<html lang>`/`dir`, interpolation, per-locale plurals, keyboard access, and
theme independence.

Two safeguards matter most and run on every CI pass:

- **Completeness** — Hindi must define every key English defines, and no
  orphans. This is why adding a key to `en.ts` fails the build until Hindi has
  it too.
- **Placeholder parity** — a translation must keep every `{placeholder}` its
  English source declares, or interpolation silently drops a value.

## Fonts

Space Grotesk is Latin-only — it has **no** Devanagari subset. The `--font-sans`
stack names platform Devanagari faces (Nirmala UI, Kohinoor Devanagari, Noto
Sans Devanagari, Lohit Devanagari) so Hindi gets a designed fallback with no
font download. Latin still resolves to Space Grotesk first, so brand type is
unchanged.
