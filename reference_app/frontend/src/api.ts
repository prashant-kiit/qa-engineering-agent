import { API_BASE_URL } from "./config";

export type Credentials = { username: string; password: string };

export type Product = { id: number; name: string; price: number };

export type CartLine = { product_id: number; quantity: number };

export type Cart = { items: CartLine[]; total: number };

export type Order = { id: number; items: CartLine[]; total: number };

/** Build the HTTP Basic `Authorization` header value for the given creds. */
export function basicAuthHeader(creds: Credentials): string {
  return "Basic " + btoa(`${creds.username}:${creds.password}`);
}

/** Default headers for an authenticated JSON request. */
export function authHeaders(creds: Credentials): Record<string, string> {
  return {
    Authorization: basicAuthHeader(creds),
    "Content-Type": "application/json",
  };
}

/** Absolute URL for a backend path. */
export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}
