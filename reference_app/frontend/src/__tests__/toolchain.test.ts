import { describe, it, expect } from "vitest";

/**
 * Sanity: proves the Vitest + jsdom toolchain itself collects and executes
 * (acceptance criterion 2 — the `test` script runs the suite). This file
 * imports no application source, so it stays green and demonstrates that any
 * red in the sibling suites is a genuine missing-implementation failure, not a
 * broken harness.
 */
describe("toolchain", () => {
  it("runs tests in an emulated DOM", () => {
    expect(typeof document).toBe("object");
    const el = document.createElement("div");
    el.textContent = "ok";
    expect(el.textContent).toBe("ok");
  });

  it("provides btoa for Basic-auth header construction", () => {
    expect(btoa("testuser:testpass")).toBe("dGVzdHVzZXI6dGVzdHBhc3M=");
  });
});
