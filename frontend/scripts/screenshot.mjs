#!/usr/bin/env node
// Headless-browser screenshot helper for visual QA in this Replit workspace.
//
// This exists because Claude-in-Chrome / a general-purpose browser tool has
// never been reliably available across sessions in this environment (see
// PROJECT_BRAIN/02_CURRENT_STATE.md's long-running "BLOCKED: no browser
// tooling" item). What IS reliably available in a Replit nix container is a
// prebuilt, correctly-linked Chromium binary at the path in
// $REPLIT_PLAYWRIGHT_CHROMIUM_EXECUTABLE — the playwright npm package's own
// downloaded browser does NOT run here (missing system shared libraries;
// this is a nix/glibc mismatch, not a playwright bug), so `executablePath`
// must point at that env var rather than letting playwright launch its
// default browser.
//
// Usage:
//   node scripts/screenshot.mjs <url> <outPath> [theme] [width] [height]
//
//   url      full URL to load, e.g. http://localhost:3000/tasks
//   outPath  where to write the PNG
//   theme    "light" | "dark" | "system" — seeds the app's theme via
//            localStorage before first paint (default: "dark", matching
//            ThemeProvider's own default in lib/theme.tsx)
//   width    viewport width in px (default 1440)
//   height   viewport height in px (default 900)
//
// Requires the app's dev server already running (`pnpm dev`, port 3000).
// Console errors, if any, are written alongside the screenshot as
// <outPath>.errors.txt.

import { chromium } from "playwright";
import { writeFileSync } from "node:fs";

const [, , url, outPath, theme = "dark", width = "1440", height = "900"] = process.argv;

if (!url || !outPath) {
  console.error("Usage: node scripts/screenshot.mjs <url> <outPath> [theme] [width] [height]");
  process.exit(1);
}

const executablePath = process.env.REPLIT_PLAYWRIGHT_CHROMIUM_EXECUTABLE;
if (!executablePath) {
  console.error(
    "REPLIT_PLAYWRIGHT_CHROMIUM_EXECUTABLE is not set — this helper only works inside a " +
      "Replit nix container that provides it. Outside Replit, install a browser and pass " +
      "its path via `executablePath` instead."
  );
  process.exit(1);
}

const browser = await chromium.launch({ executablePath, args: ["--no-sandbox"] });
const context = await browser.newContext({
  viewport: { width: parseInt(width, 10), height: parseInt(height, 10) },
});
await context.addInitScript((t) => {
  try {
    localStorage.setItem("agent-os:theme", t);
  } catch {
    /* ignore */
  }
}, theme);

const page = await context.newPage();
const errors = [];
page.on("console", (msg) => {
  if (msg.type() === "error") errors.push(msg.text());
});
page.on("pageerror", (err) => errors.push(String(err)));

await page.goto(url, { waitUntil: "networkidle" });
await page.waitForTimeout(600);
await page.screenshot({ path: outPath });

if (errors.length) {
  writeFileSync(`${outPath}.errors.txt`, errors.join("\n"));
  console.log(`Wrote ${outPath} (${errors.length} console error(s) — see ${outPath}.errors.txt)`);
} else {
  console.log(`Wrote ${outPath} (no console errors)`);
}

await browser.close();
