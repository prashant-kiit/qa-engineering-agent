import { test, expect } from '@playwright/test';
import { authHeader, BACKEND_URL, emptyCart } from './helpers';

/**
 * Baseline **API** test — the order-retrieval endpoint must enforce auth.
 *
 * Uses Playwright's `request` fixture (a Node HTTP client, not the browser) so it
 * can issue `GET /orders/{id}` with MISSING and with INVALID Basic credentials —
 * something the UI can never do (the frontend always sends the logged-in user's
 * credentials). The clean-backend invariant is: every order endpoint requires
 * auth (401 without / with-invalid credentials).
 *
 * Discriminating for the `order_auth_bypass` variant: there `GET /orders/{id}`
 * returns HTTP 200 without valid credentials, so both 401 assertions fail — this
 * is the ONLY baseline test that can catch bug (c). Passes on clean and on the
 * `checkout_total` / `cart_quantity` variants (they leave order-endpoint auth
 * enforced).
 */

const INVALID_AUTH =
  'Basic ' + Buffer.from('testuser:wrongpass').toString('base64');

test('order endpoint enforces auth: GET /orders/{id} is 401 without/with-invalid credentials', async ({
  request,
}) => {
  // Create an order first, WITH valid credentials (creation is not the fault axis).
  await emptyCart(request);

  const prods = await request.get(`${BACKEND_URL}/products`, {
    headers: { Authorization: authHeader() },
  });
  expect(prods.status(), 'GET /products should be 200 with valid auth').toBe(200);
  const products = await prods.json();
  expect(Array.isArray(products) && products.length > 0).toBe(true);
  const productId = products[0].id;

  const add = await request.post(`${BACKEND_URL}/cart/items`, {
    headers: { Authorization: authHeader() },
    data: { product_id: productId, quantity: 1 },
  });
  expect([200, 201]).toContain(add.status());

  const checkout = await request.post(`${BACKEND_URL}/checkout`, {
    headers: { Authorization: authHeader() },
  });
  expect([200, 201]).toContain(checkout.status());
  const order = await checkout.json();
  expect(order.id, 'checkout should return an order id').toBeTruthy();

  // Load-bearing, non-vacuous assertions on the app's HTTP status:
  // (1) NO credentials -> must be 401.
  const noCreds = await request.get(`${BACKEND_URL}/orders/${order.id}`);
  expect(
    noCreds.status(),
    'GET /orders/{id} without credentials must be 401'
  ).toBe(401);

  // (2) INVALID credentials -> must also be 401.
  const badCreds = await request.get(`${BACKEND_URL}/orders/${order.id}`, {
    headers: { Authorization: INVALID_AUTH },
  });
  expect(
    badCreds.status(),
    'GET /orders/{id} with invalid credentials must be 401'
  ).toBe(401);
});
