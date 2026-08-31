import { describe, it, expect } from "vitest";
import { getDeploymentEnvironment, getEnvironmentLabel } from "./environment";

describe("getDeploymentEnvironment", () => {
  it("recognises production", () => {
    expect(getDeploymentEnvironment("app.thynact.com")).toBe("production");
  });

  it("recognises staging", () => {
    expect(getDeploymentEnvironment("staging.thynact.com")).toBe("staging");
  });

  it("recognises Cloudflare previews", () => {
    expect(getDeploymentEnvironment("abc.agent-os-test.pages.dev")).toBe("preview");
  });

  it("recognises local development", () => {
    expect(getDeploymentEnvironment("localhost")).toBe("local");
  });

  it("treats an unknown host as non-production", () => {
    expect(getDeploymentEnvironment("staging.thynact.com.evil.example")).not.toBe("production");
  });
});

describe("getEnvironmentLabel", () => {
  it("shows no badge in production", () => {
    expect(getEnvironmentLabel("app.thynact.com")).toBeNull();
  });

  it("labels every non-production deployment", () => {
    expect(getEnvironmentLabel("staging.thynact.com")).toBe("STAGING");
    expect(getEnvironmentLabel("x.pages.dev")).toBe("PREVIEW");
    expect(getEnvironmentLabel("localhost")).toBe("LOCAL");
  });
});
