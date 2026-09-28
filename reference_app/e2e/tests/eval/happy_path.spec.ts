import { test, expect } from '@playwright/test';
import { emptyCart, login, parseMoney } from './helpers';

/**
 * Baseline UI test — happy path: the order-confirmation total must equal the
 * pre-checkout cart total (backend invariant total = Σ price × quantity).
 *
 * Discriminating for the `checkout_total` variant: there the checkout response
 * total is offset, so order-total != cart-total and this assertion fails.
 * Passes on clean and on the other two variants (they leave checkout maths
 * intact).
 */

test.beforeEach(async ({ request }) => {
  await emptyCart(request);
});

test('happy path: order total equals cart total', async ({ page }) => {
  await login(page);

  // Add one product; the running cart-count reflects the successful add.
  await page.getByTestId('add-to-cart').first().click();
  await expect(page.getByTestId('cart-count')).toHaveText(/\b1\b/);

  // View the cart and read its (correct) total.
  await page.getByRole('button', { name: 'Cart', exact: true }).click();
  await expect(page.getByTestId('cart-line').first()).toBeVisible();
  const cartTotal = parseMoney(await page.getByTestId('cart-total').textContent());
  expect(cartTotal).toBeGreaterThan(0);

  // Checkout and read the order-confirmation total.
  await page.getByTestId('cart-checkout').click();
  await page.getByTestId('checkout-submit').click();
  await expect(page.getByRole('heading', { name: 'Order confirmed' })).toBeVisible();
  await expect(page.getByTestId('checkout-error')).toHaveCount(0);

  const orderTotal = parseMoney(await page.getByTestId('order-total').textContent());
  // Load-bearing, non-vacuous assertion on an app-produced value.
  expect(orderTotal).toBeGreaterThan(0);
  expect(orderTotal).toBeCloseTo(cartTotal, 2);
});
