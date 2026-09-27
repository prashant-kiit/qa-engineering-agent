/**
 * API base URL configuration (acceptance criterion 16).
 *
 * Resolved from the Vite env var `VITE_API_BASE_URL` so the target backend can
 * be changed without editing component source. Defaults to the backend's
 * documented base URL when nothing is overridden.
 */
export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  "http://127.0.0.1:8000";
