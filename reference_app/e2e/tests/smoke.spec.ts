import { test, expect, Page } from '@playwright/test';

/**
 * Phase-0 end-to-end smoke test for the reference shop app.
 *
 * Drives the full happy path through the real browser UI against the running
 * reference app (backend + frontend launched by Playwright's `webServer`):
 *
 *   login -> add-to-cart -> view cart -> checkout -> order confirmation
 *
 * Load-bearing assertion: the order-confirmation `order-total` MUST equal the
 * cart `cart-total` read immediately before checkout (backend invariant
 * total = Σ price × quantity). Under the developer-owned `SMOKE_FAULT=1`
 * toggle the app surfaces a wrong order total, so this equality assertion
 * fails and the run exits non-zero (the Phase-0 "red on buggy" demonstration).
 *
 * Selectors, routes, credentials, and ports are taken from the pinned
 * contracts in `.harness/tasks/p0-playwright-smoke.md`,
 * `.harness/tasks/p0-shop-frontend.md`, and `.harness/tasks/p0-shop-backend.md`.
 * This spec does NOT know or depend on the implementation internals.
 */

const USERNAME = 'testuser';
const PASSWORD = 'testpass';

/** Parse a currency/number string (e.g. "$12.50", "12.50", "12") to a number. */
function parseMoney(raw: string | null): number {
  expect(raw, 'expected a text value to parse as a number').not.toBeNull();
  const text = (raw as string).trim();
  const match = text.match(/-?\d+(?:[.,]\d+)?/);
  expect(match, `expected a numeric value in "${text}"`).not.toBeNull();
  const normalized = (match as RegExpMatchArray)[0].replace(',', '.');
  const value = Number(normalized);
  expect(Number.isNaN(value), `parsed a non-number from "${text}"`).toBe(false);
  return value;
}

async function login(page: Page): Promise<void> {
  await page.goto('/');
  await page.getByTestId('login-username').fill(USERNAME);
  await page.getByTestId('login-password').fill(PASSWORD);
  await page.getByTestId('login-submit').click();

  // Reached the authenticated shop: product list visible, no login error.
  await expect(page.getByTestId('product-item').first()).toBeVisible();
  await expect(page.getByTestId('login-error')).toHaveCount(0);
}

test('smoke: login -> add to cart -> checkout, order total equals cart total', async ({ page }) => {
  // 3b. Authenticate and confirm we reached the authenticated shop.
  await login(page);

  // 3c. Add a product to the cart and confirm cart-count reflects the add.
  await page.getByTestId('add-to-cart').first().click();
  await expect(page.getByTestId('cart-count')).toHaveText(/\b1\b/);

  // 3d. Navigate to the cart; confirm at least one line and read a positive total.
  //     `exact: true` targets ONLY the nav button whose accessible name is exactly
  //     "Cart" — Playwright's default (case-insensitive substring) name match would
  //     otherwise also match the five "Add to cart" product buttons (strict-mode
  //     violation: "resolved to 6 elements"). The clean frontend labels the nav button
  //     "Cart" and the product buttons "Add to cart", so exact-match disambiguates.
  await page.getByRole('button', { name: 'Cart', exact: true }).click();
  await expect(page.getByTestId('cart-line').first()).toBeVisible();
  const cartLineCount = await page.getByTestId('cart-line').count();
  expect(cartLineCount).toBeGreaterThanOrEqual(1);

  const cartTotal = parseMoney(await page.getByTestId('cart-total').textContent());
  expect(cartTotal).toBeGreaterThan(0);

  // 3e. Proceed to checkout and place the order.
  await page.getByTestId('cart-checkout').click();
  await page.getByTestId('checkout-submit').click();

  // 4a. Order-confirmation heading is visible; no checkout error.
  await expect(page.getByRole('heading', { name: 'Order confirmed' })).toBeVisible();
  await expect(page.getByTestId('checkout-error')).toHaveCount(0);

  // 4b. order-id is present and non-empty.
  await expect(page.getByTestId('order-id')).toBeVisible();
  const orderId = (await page.getByTestId('order-id').textContent())?.trim() ?? '';
  expect(orderId.length).toBeGreaterThan(0);

  // 4c. Load-bearing assertion: order-total is positive AND equals the
  //     pre-checkout cart total (enforces total = Σ price × quantity).
  const orderTotal = parseMoney(await page.getByTestId('order-total').textContent());
  expect(orderTotal).toBeGreaterThan(0);
  expect(orderTotal).toBeCloseTo(cartTotal, 2);
});
