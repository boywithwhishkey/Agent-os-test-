import { describe, it, expect } from "vitest";
import { computeApiBaseUrl } from "./config";

// The isolation rule these lock in: only the real production hostname may
// resolve to the production API. Everything else — staging, previews, and any
// unexpected host — must fall back to staging, so a misconfigured deployment
// fails safe instead of reaching production data.
describe("computeApiBaseUrl", () => {
  it("routes the production host to the production API", () => {
    expect(computeApiBaseUrl("app.thynact.com")).toBe("https://api.thynact.com");
  });

  it("routes staging to the staging API", () => {
    expect(computeApiBaseUrl("staging.thynact.com")).toBe("https://api-staging.thynact.com");
  });

  it("routes Cloudflare preview deployments to staging, never production", () => {
    expect(computeApiBaseUrl("abc123.thynact.pages.dev")).toBe("https://api-staging.thynact.com");
  });

  it("falls back to staging for an unknown host", () => {
    expect(computeApiBaseUrl("something-unexpected.example.com")).toBe(
      "https://api-staging.thynact.com"
    );
  });

  it("never returns the production API for anything but the production host", () => {
    const hosts = [
      "staging.thynact.com",
      "preview.thynact.pages.dev",
      "app.thynact.com.evil.example",
      "localhost",
      "",
    ];
    for (const host of hosts) {
      expect(computeApiBaseUrl(host)).not.toBe("https://api.thynact.com");
    }
  });
});
