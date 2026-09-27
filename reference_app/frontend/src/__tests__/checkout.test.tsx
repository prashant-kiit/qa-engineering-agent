import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { CheckoutView, OrderConfirmationView } from "../views";
import {
  installFetch,
  jsonResponse,
  headerOf,
  basicHeader,
  findCall,
  TEST_CREDS,
} from "../test/helpers";

/**
 * CheckoutView contract (Tester-defined):
 *   import { CheckoutView } from "../views"
 *   props: { credentials: {username,password} }
 *   testids: checkout-submit (activates checkout), checkout-error (error state),
 *            order-id + order-total (shown once the confirmation renders on success)
 * Activating checkout POSTs /checkout with Basic auth; on success it renders the
 * order-confirmation showing the returned order id + total; on client error it
 * surfaces an error and shows no fabricated order.
 *
 * OrderConfirmationView contract:
 *   import { OrderConfirmationView } from "../views"
 *   props: { order: { id, total, items } }
 *   testids: order-id, order-total
 */
const ORDER = { id: 4242, items: [{ product_id: 1, quantity: 2 }], total: 39.48 };

describe("CheckoutView -> order confirmation", () => {
  it("POSTs /checkout with Basic auth when activated (criterion 13)", async () => {
    const { calls } = installFetch((url, init) => {
      const method = (init.method || "GET").toUpperCase();
      if (url.includes("/checkout") && method === "POST") return jsonResponse(ORDER, 201);
      return jsonResponse({}, 200);
    });
    render(<CheckoutView credentials={TEST_CREDS} />);

    fireEvent.click(await screen.findByTestId("checkout-submit"));

    await waitFor(() => expect(findCall(calls, "POST", "/checkout")).toBeTruthy());
    const post = findCall(calls, "POST", "/checkout")!;
    expect(headerOf(post.init, "Authorization")).toBe(basicHeader(TEST_CREDS));
  });

  it("renders the order-confirmation with the returned id and total on success (criterion 14)", async () => {
    installFetch((url, init) => {
      const method = (init.method || "GET").toUpperCase();
      if (url.includes("/checkout") && method === "POST") return jsonResponse(ORDER, 201);
      return jsonResponse({}, 200);
    });
    render(<CheckoutView credentials={TEST_CREDS} />);

    fireEvent.click(await screen.findByTestId("checkout-submit"));

    await waitFor(() =>
      expect(screen.getByTestId("order-id")).toHaveTextContent(String(ORDER.id))
    );
    expect(screen.getByTestId("order-total")).toHaveTextContent("39.48");
  });

  it("surfaces an error and shows no fabricated order when checkout fails (criterion 15)", async () => {
    installFetch((url, init) => {
      const method = (init.method || "GET").toUpperCase();
      if (url.includes("/checkout") && method === "POST")
        return jsonResponse({ detail: "Cart is empty" }, 400);
      return jsonResponse({}, 200);
    });
    render(<CheckoutView credentials={TEST_CREDS} />);

    fireEvent.click(await screen.findByTestId("checkout-submit"));

    await waitFor(() =>
      expect(screen.getByTestId("checkout-error")).toBeInTheDocument()
    );
    expect(screen.queryByTestId("order-id")).toBeNull();
  });
});

describe("OrderConfirmationView", () => {
  it("displays the order id and total from its order prop (criterion 14, 17)", () => {
    render(<OrderConfirmationView order={ORDER} />);
    expect(screen.getByTestId("order-id")).toHaveTextContent(String(ORDER.id));
    expect(screen.getByTestId("order-total")).toHaveTextContent("39.48");
  });
});
