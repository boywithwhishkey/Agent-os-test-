import { describe, it, expect, afterEach } from "vitest";
import { screen, fireEvent, cleanup } from "@testing-library/react";
import { renderWithProviders } from "@/test/utils";
import Settings from "./Settings";
import { getApiKey, resetApiConfig } from "@/lib/api/config";

describe("Settings page", () => {
  afterEach(() => {
    resetApiConfig();
    cleanup();
  });

  it("saves the API key to sessionStorage only, not localStorage", () => {
    renderWithProviders(<Settings />);

    fireEvent.change(screen.getByLabelText(/api key/i), { target: { value: "secret-key" } });
    fireEvent.click(screen.getByRole("button", { name: /save configuration/i }));

    expect(getApiKey()).toBe("secret-key");
    expect(localStorage.getItem("agent-os:api-key")).toBeNull();
  });

  it("clears the configuration", () => {
    renderWithProviders(<Settings />);
    fireEvent.change(screen.getByLabelText(/api key/i), { target: { value: "secret-key" } });
    fireEvent.click(screen.getByRole("button", { name: /save configuration/i }));

    fireEvent.click(screen.getByRole("button", { name: /^clear$/i }));
    expect(getApiKey()).toBe("");
  });
});
