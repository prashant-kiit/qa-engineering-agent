import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { ProductListView } from "../views";
import {
  installFetch,
  jsonResponse,
  headerOf,
  bodyOf,
  basicHeader,
  findCall,
  TEST_CREDS,
} from "../test/helpers";

/**
 * ProductListView contract (Tester-defined):
 *   import { ProductListView } from "../views"
 *   props: { credentials: {username,password} }
 *   testids: product-item (one per product, each contains its name + price text),
 *            add-to-cart (a control within each product-item),
 *            cart-count (reflects that items were added)
 * On mount it GETs /products with Basic auth; add-to-cart POSTs /cart/items
 * { product_id, quantity>=1 } with Basic auth.
 */
const CATALOG = [
  { id: 1, name: "Widget", price: 9.99 },
  { id: 2, name: "Gadget", price: 19.5 },
  { id: 3, name: "Gizmo", price: 4.25 },
];

function stub() {
  return installFetch((url, init) => {
    const method = (init.method || "GET").toUpperCase();
    if (url.includes("/products") && method === "GET") {
      return jsonResponse(CATALOG, 200);
    }
    if (url.includes("/cart/items") && method === "POST") {
      const b = bodyOf(init);
      return jsonResponse(
        { items: [{ product_id: b.product_id, quantity: b.quantity }], total: 9.99 },
        201
      );
    }
    if (url.includes("/cart") && method === "GET") {
      return jsonResponse({ items: [], total: 0 }, 200);
    }
    return jsonResponse({}, 200);
  });
}

describe("ProductListView", () => {
  it("renders one entry per product with name and price (criterion 6, 17)", async () => {
    stub();
    render(<ProductListView credentials={TEST_CREDS} />);

    await waitFor(() =>
      expect(screen.getAllByTestId("product-item")).toHaveLength(CATALOG.length)
    );
    for (const p of CATALOG) {
      expect(screen.getByText(new RegExp(p.name))).toBeInTheDocument();
      expect(screen.getByText(new RegExp(String(p.price)))).toBeInTheDocument();
    }
  });

  it("fetches the catalog from GET /products with Basic auth (criterion 7)", async () => {
    const { calls } = stub();
    render(<ProductListView credentials={TEST_CREDS} />);

    await waitFor(() => expect(findCall(calls, "GET", "/products")).toBeTruthy());
    const call = findCall(calls, "GET", "/products")!;
    expect(headerOf(call.init, "Authorization")).toBe(basicHeader(TEST_CREDS));
  });

  it("add-to-cart POSTs /cart/items with the product_id and a positive quantity (criterion 8)", async () => {
    const { calls } = stub();
    render(<ProductListView credentials={TEST_CREDS} />);

    await waitFor(() =>
      expect(screen.getAllByTestId("product-item")).toHaveLength(CATALOG.length)
    );
    const firstItem = screen.getAllByTestId("product-item")[0];
    fireEvent.click(within(firstItem).getByTestId("add-to-cart"));

    await waitFor(() => expect(findCall(calls, "POST", "/cart/items")).toBeTruthy());
    const post = findCall(calls, "POST", "/cart/items")!;
    expect(headerOf(post.init, "Authorization")).toBe(basicHeader(TEST_CREDS));
    const body = bodyOf(post.init);
    expect(body.product_id).toBe(CATALOG[0].id);
    expect(body.quantity).toBeGreaterThanOrEqual(1);
  });

  it("reflects the added item after a successful add (criterion 9)", async () => {
    stub();
    render(<ProductListView credentials={TEST_CREDS} />);

    await waitFor(() =>
      expect(screen.getAllByTestId("product-item")).toHaveLength(CATALOG.length)
    );
    const firstItem = screen.getAllByTestId("product-item")[0];
    fireEvent.click(within(firstItem).getByTestId("add-to-cart"));

    await waitFor(() =>
      expect(screen.getByTestId("cart-count")).toHaveTextContent(/[1-9]/)
    );
  });
});
