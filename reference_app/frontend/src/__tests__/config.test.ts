import { describe, it, expect } from "vitest";

/**
 * Acceptance criterion 16 — the API base URL is configurable without editing
 * component source and DEFAULTS to the backend's documented base URL.
 *
 * Binding export point (Tester-defined contract for the Developer):
 *   src/config.ts must export `API_BASE_URL: string`, resolved from the
 *   `VITE_API_BASE_URL` env var and defaulting to http://127.0.0.1:8000.
 */
describe("API base URL configuration (criterion 16)", () => {
  it("exports a configuration point that defaults to the documented backend URL", async () => {
    const mod = await import("../config");
    expect(mod.API_BASE_URL).toBe("http://127.0.0.1:8000");
  });
});
