import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { CartView } from "../views";
import { installFetch, jsonResponse, TEST_CREDS } from "../test/helpers";

/**
 * CartView contract (Tester-defined):
 *   import { CartView } from "../views"
 *   props: { credentials: {username,password} }
 *   testids: cart-line (one per line item), cart-total (shows computed total),
 *            cart-empty (empty-cart state), cart-checkout (proceed-to-checkout control)
 * On mount it GETs /cart with Basic auth.
 */
describe("CartView", () => {
  it("renders each line item and the cart total from GET /cart (criterion 10)", async () => {
    installFetch(() =>
      jsonResponse(
        {
          items: [
            { product_id: 1, quantity: 2 },
            { product_id: 2, quantity: 1 },
          ],
          total: 39.48,
        },
        200
      )
    );
    render(<CartView credentials={TEST_CREDS} />);

    await waitFor(() =>
      expect(screen.getAllByTestId("cart-line")).toHaveLength(2)
    );
    // quantities are visible on their lines
    const lines = screen.getAllByTestId("cart-line").map((n) => n.textContent || "");
    expect(lines.join(" ")).toMatch(/2/);
    expect(lines.join(" ")).toMatch(/1/);
    // exact total pinned by the stub
    expect(screen.getByTestId("cart-total")).toHaveTextContent("39.48");
  });

  it("renders a clear empty-cart state with no phantom lines (criterion 11)", async () => {
    installFetch(() => jsonResponse({ items: [], total: 0 }, 200));
    render(<CartView credentials={TEST_CREDS} />);

    await waitFor(() =>
      expect(screen.getByTestId("cart-empty")).toBeInTheDocument()
    );
    expect(screen.queryAllByTestId("cart-line")).toHaveLength(0);
  });

  it("exposes a proceed-to-checkout control (criterion 12, 17)", async () => {
    installFetch(() =>
      jsonResponse({ items: [{ product_id: 1, quantity: 1 }], total: 9.99 }, 200)
    );
    render(<CartView credentials={TEST_CREDS} />);

    await waitFor(() =>
      expect(screen.getByTestId("cart-checkout")).toBeInTheDocument()
    );
  });
});
