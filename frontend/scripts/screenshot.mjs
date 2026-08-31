#!/usr/bin/env node
// Headless-browser screenshot helper for THYNACT frontend visual QA.
//
// UI work is not complete because the React/CSS "looks right" — this project
// accumulated several sessions of reasoned-but-never-rendered visual changes.
// Run this against a real dev server and actually look at the output.
//
// Browser resolution is deliberately portable (an earlier version hard-required
// a Replit-specific env var and simply exited everywhere else). Order:
//   1. THYNACT_CHROMIUM_EXECUTABLE            (explicit override, if it exists)
//   2. REPLIT_PLAYWRIGHT_CHROMIUM_EXECUTABLE  (back-compat, if it exists)
//   3. $PLAYWRIGHT_BROWSERS_PATH/chromium*    (Claude cloud ships /opt/pw-browsers)
//   4. playwright's own managed Chromium      (plain launch, no executablePath)
//   5. common system chromium/chrome paths
//   6. actionable failure message listing everything that was tried
//
// Usage:
//   node scripts/screenshot.mjs <url> <outPath> [theme] [width] [height]
//
//   url      full URL to load, e.g. http://localhost:3000/tasks
//   outPath  where to write the PNG
//   theme    "light" | "dark" | "system" — seeded into localStorage before
//            first paint (default: "dark", matching ThemeProvider's default)
//   width    viewport width in px (default 1440)
//   height   viewport height in px (default 900)
//
// Requires the dev server already running (`pnpm dev`, port 3000).
// Console errors, if any, are written to <outPath>.errors.txt.
// Exits non-zero if the page overflows horizontally, so responsive
// regressions fail loudly instead of needing a human to notice.

import { chromium } from "playwright";
import { writeFileSync, existsSync, readdirSync } from "node:fs";
import { join } from "node:path";

const [, , url, outPath, theme = "dark", width = "1440", height = "900"] = process.argv;

if (!url || !outPath) {
  console.error("Usage: node scripts/screenshot.mjs <url> <outPath> [theme] [width] [height]");
  process.exit(1);
}

const tried = [];

function candidateFromEnv(name) {
  const value = process.env[name];
  if (!value) {
    tried.push(`${name}: not set`);
    return null;
  }
  if (!existsSync(value)) {
    tried.push(`${name}=${value}: path does not exist`);
    return null;
  }
  return value;
}

// Playwright installs browsers as <root>/chromium-<build>/chrome-linux/chrome.
// Claude cloud additionally symlinks <root>/chromium straight at the binary.
function candidatesFromBrowsersPath() {
  const root = process.env.PLAYWRIGHT_BROWSERS_PATH;
  if (!root || !existsSync(root)) {
    tried.push(`PLAYWRIGHT_BROWSERS_PATH: ${root ? "path does not exist" : "not set"}`);
    return [];
  }
  const found = [];
  const direct = join(root, "chromium");
  if (existsSync(direct)) found.push(direct);
  for (const entry of readdirSync(root)) {
    if (!entry.startsWith("chromium")) continue;
    for (const rel of ["chrome-linux/chrome", "chrome-linux/headless_shell"]) {
      const full = join(root, entry, rel);
      if (existsSync(full)) found.push(full);
    }
  }
  if (!found.length) tried.push(`PLAYWRIGHT_BROWSERS_PATH=${root}: no chromium build found`);
  return found;
}

const SYSTEM_PATHS = [
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
  "/usr/bin/google-chrome",
  "/usr/bin/google-chrome-stable",
];

async function launch() {
  const explicit = [
    candidateFromEnv("THYNACT_CHROMIUM_EXECUTABLE"),
    candidateFromEnv("REPLIT_PLAYWRIGHT_CHROMIUM_EXECUTABLE"),
    ...candidatesFromBrowsersPath(),
  ].filter(Boolean);

  for (const executablePath of explicit) {
    try {
      const browser = await chromium.launch({ executablePath, args: ["--no-sandbox"] });
      console.log(`Using Chromium: ${executablePath}`);
      return browser;
    } catch (err) {
      tried.push(`${executablePath}: ${err.message.split("\n")[0]}`);
    }
  }

  // Playwright-managed browser (whatever `playwright install` put in place).
  try {
    const browser = await chromium.launch({ args: ["--no-sandbox"] });
    console.log("Using Chromium: playwright-managed default");
    return browser;
  } catch (err) {
    tried.push(`playwright-managed default: ${err.message.split("\n")[0]}`);
  }

  for (const executablePath of SYSTEM_PATHS) {
    if (!existsSync(executablePath)) continue;
    try {
      const browser = await chromium.launch({ executablePath, args: ["--no-sandbox"] });
      console.log(`Using Chromium: ${executablePath}`);
      return browser;
    } catch (err) {
      tried.push(`${executablePath}: ${err.message.split("\n")[0]}`);
    }
  }

  console.error(
    "No usable Chromium found. Tried, in order:\n  " +
      tried.join("\n  ") +
      "\n\nFix by either:\n" +
      "  - setting THYNACT_CHROMIUM_EXECUTABLE to a Chromium/Chrome binary, or\n" +
      "  - running `pnpm exec playwright install chromium` to fetch a managed one."
  );
  process.exit(1);
}

const browser = await launch();
const context = await browser.newContext({
  viewport: { width: parseInt(width, 10), height: parseInt(height, 10) },
});
// Seed theme, and optionally the operator session, before first paint.
// Without the session seed every page renders its unauthenticated state, which
// is why earlier visual QA could never check real data-bearing screens. The key
// is read from the environment and never written to disk or committed — use a
// local dev key, never a production one.
await context.addInitScript(
  ({ t, baseUrl, apiKey }) => {
    try {
      localStorage.setItem("agent-os:theme", t);
      if (baseUrl) sessionStorage.setItem("agent-os:api-base-url", baseUrl);
      if (apiKey) sessionStorage.setItem("agent-os:api-key", apiKey);
    } catch {
      /* storage unavailable */
    }
  },
  {
    t: theme,
    baseUrl: process.env.THYNACT_SCREENSHOT_API_BASE_URL || "",
    apiKey: process.env.THYNACT_SCREENSHOT_API_KEY || "",
  }
);

const page = await context.newPage();
const errors = [];
page.on("console", (msg) => {
  if (msg.type() === "error") errors.push(msg.text());
});
page.on("pageerror", (err) => errors.push(String(err)));

await page.goto(url, { waitUntil: "networkidle" });
await page.waitForTimeout(600);
await page.screenshot({ path: outPath });

// Page-level horizontal overflow is the responsive defect this project keeps
// shipping unseen; check it programmatically rather than trusting the eye.
const overflow = await page.evaluate(() => ({
  scrollWidth: document.documentElement.scrollWidth,
  clientWidth: document.documentElement.clientWidth,
}));
const overflows = overflow.scrollWidth > overflow.clientWidth;

if (errors.length) writeFileSync(`${outPath}.errors.txt`, errors.join("\n"));

const parts = [`Wrote ${outPath} at ${width}x${height} (${theme})`];
parts.push(errors.length ? `${errors.length} console error(s) -> ${outPath}.errors.txt` : "no console errors");
parts.push(
  overflows
    ? `HORIZONTAL OVERFLOW: scrollWidth ${overflow.scrollWidth} > clientWidth ${overflow.clientWidth}`
    : "no horizontal overflow"
);
console.log(parts.join(" | "));

await browser.close();
process.exit(overflows ? 2 : 0);
