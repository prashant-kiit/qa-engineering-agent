import { APIRequestContext, expect, Page } from '@playwright/test';

/**
 * Shared helpers for the eval **baseline** suite (unit `p0-eval-harness`).
 *
 * The baseline is a small hand-written TS-Playwright suite (UI + API) that:
 *   - PASSES against the clean variant (EVAL_BUG unset / none), and
 *   - as a whole, produces >=1 genuine assertion failure on each buggy variant.
 *
 * Selectors, routes, credentials and ports come from the pinned p0-shop-backend /
 * p0-shop-frontend / p0-playwright-smoke contracts.
 */

export const BACKEND_URL = 'http://127.0.0.1:8000';
export const USERNAME = 'testuser';
export const PASSWORD = 'testpass';

/** HTTP Basic `Authorization` header value for the seeded test account. */
export function authHeader(): string {
  return 'Basic ' + Buffer.from(`${USERNAME}:${PASSWORD}`).toString('base64');
}

/** Parse a currency/number string (e.g. "$12.50", "12.50", "12") to a number. */
export function parseMoney(raw: string | null): number {
  expect(raw, 'expected a text value to parse as a number').not.toBeNull();
  const text = (raw as string).trim();
  const match = text.match(/-?\d+(?:[.,]\d+)?/);
  expect(match, `expected a numeric value in "${text}"`).not.toBeNull();
  const normalized = (match as RegExpMatchArray)[0].replace(',', '.');
  const value = Number(normalized);
  expect(Number.isNaN(value), `parsed a non-number from "${text}"`).toBe(false);
  return value;
}

/** Authenticate through the UI and confirm we reached the authenticated shop. */
export async function login(page: Page): Promise<void> {
  await page.goto('/');
  await page.getByTestId('login-username').fill(USERNAME);
  await page.getByTestId('login-password').fill(PASSWORD);
  await page.getByTestId('login-submit').click();
  await expect(page.getByTestId('product-item').first()).toBeVisible();
  await expect(page.getByTestId('login-error')).toHaveCount(0);
}

/**
 * Drain the test user's cart via the backend API so each test starts from a
 * known-empty cart (there is no dedicated clear-cart endpoint; checkout empties
 * a non-empty cart). Keeps the UI cart-quantity / total assertions independent
 * of test ordering.
 */
export async function emptyCart(request: APIRequestContext): Promise<void> {
  const res = await request.get(`${BACKEND_URL}/cart`, {
    headers: { Authorization: authHeader() },
  });
  if (!res.ok()) return;
  const cart = await res.json();
  if (cart.items && cart.items.length > 0) {
    await request.post(`${BACKEND_URL}/checkout`, {
      headers: { Authorization: authHeader() },
    });
  }
}

/** Fetch the seeded catalog (Basic auth) and return the first product. */
export async function firstProduct(
  request: APIRequestContext
): Promise<{ id: number; name: string; price: number }> {
  const res = await request.get(`${BACKEND_URL}/products`, {
    headers: { Authorization: authHeader() },
  });
  expect(res.status(), 'GET /products should be 200 with valid auth').toBe(200);
  const products = await res.json();
  expect(Array.isArray(products) && products.length > 0).toBe(true);
  return products[0];
}
