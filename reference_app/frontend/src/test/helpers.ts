import { vi } from "vitest";

/**
 * Test helpers for the reference-shop frontend component/integration suite.
 *
 * The frontend talks to the shop backend over the global `fetch` API using HTTP
 * Basic Auth. These helpers stub `fetch` with canned responses matching the
 * binding backend contract (see .harness/tasks/p0-shop-backend.md) so no real
 * backend is contacted during `npm test`.
 */

export type Credentials = { username: string; password: string };

export const TEST_CREDS: Credentials = {
  username: "testuser",
  password: "testpass",
};

/** The exact Basic Authorization header value for the seeded account. */
export function basicHeader(creds: Credentials = TEST_CREDS): string {
  return "Basic " + btoa(`${creds.username}:${creds.password}`);
}

/** A minimal fetch Response stand-in that supports the shapes views consume. */
export function jsonResponse(body: unknown, status = 200): Response {
  const headers = new Headers({ "Content-Type": "application/json" });
  if (status === 401) headers.set("WWW-Authenticate", "Basic");
  return {
    ok: status >= 200 && status < 300,
    status,
    headers,
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as unknown as Response;
}

export type FetchCall = { url: string; init: RequestInit };

/**
 * Install a routed fetch mock. `handler(url, init)` returns the Response for a
 * request, letting a single view fire several calls (e.g. GET /products then
 * POST /cart/items) in one test. All calls are recorded on the returned array.
 */
export function installFetch(
  handler: (url: string, init: RequestInit) => Response | Promise<Response>
): { calls: FetchCall[]; mock: ReturnType<typeof vi.fn> } {
  const calls: FetchCall[] = [];
  const mock = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = typeof input === "string" ? input : input.toString();
    calls.push({ url, init });
    return handler(url, init);
  });
  vi.stubGlobal("fetch", mock);
  return { calls, mock };
}

/** Read a header off a recorded request whether headers were an object or Headers. */
export function headerOf(init: RequestInit | undefined, name: string): string | null {
  if (!init || !init.headers) return null;
  const h = init.headers;
  if (h instanceof Headers) return h.get(name);
  if (Array.isArray(h)) {
    const found = h.find(([k]) => k.toLowerCase() === name.toLowerCase());
    return found ? found[1] : null;
  }
  const rec = h as Record<string, string>;
  const key = Object.keys(rec).find((k) => k.toLowerCase() === name.toLowerCase());
  return key ? rec[key] : null;
}

/** Parse a recorded request body (JSON string) into an object. */
export function bodyOf(init: RequestInit | undefined): any {
  if (!init || init.body == null) return undefined;
  if (typeof init.body === "string") return JSON.parse(init.body);
  return init.body;
}

/** Find the first recorded call whose method + url path match. */
export function findCall(
  calls: FetchCall[],
  method: string,
  pathIncludes: string
): FetchCall | undefined {
  return calls.find((c) => {
    const m = (c.init.method || "GET").toUpperCase();
    return m === method.toUpperCase() && c.url.includes(pathIncludes);
  });
}
