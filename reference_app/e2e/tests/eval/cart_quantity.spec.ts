import { test, expect } from '@playwright/test';
import { emptyCart, firstProduct, login, parseMoney } from './helpers';

/**
 * Baseline UI test — cart quantity accumulates on repeat add: adding the same
 * product twice (quantity 1 each) must report quantity 2 and a cart total of
 * price × 2.
 *
 * Discriminating for the `cart_quantity` variant: there the repeat add does not
 * accumulate, so the quantity stays 1 and the total stays price × 1 — both
 * assertions fail. Passes on clean and on the other two variants.
 */

test.beforeEach(async ({ request }) => {
  await emptyCart(request);
});

test('cart quantity accumulates: adding a product twice yields quantity 2', async ({
  page,
  request,
}) => {
  const product = await firstProduct(request);
  const expectedTotal = product.price * 2;

  await login(page);

  // Add the SAME (first) product twice; the local cart-count reflects two adds.
  await page.getByTestId('add-to-cart').first().click();
  await page.getByTestId('add-to-cart').first().click();
  await expect(page.getByTestId('cart-count')).toHaveText(/\b2\b/);

  // Inspect the cart: exactly one line for that product, quantity 2, total = price×2.
  await page.getByRole('button', { name: 'Cart', exact: true }).click();
  await expect(page.getByTestId('cart-line').first()).toBeVisible();

  const firstLineText = (await page.getByTestId('cart-line').first().textContent()) ?? '';
  // Non-vacuous assertion on the app-reported quantity.
  expect(firstLineText).toMatch(/Qty:\s*2\b/);

  const cartTotal = parseMoney(await page.getByTestId('cart-total').textContent());
  expect(cartTotal).toBeCloseTo(expectedTotal, 2);
});
