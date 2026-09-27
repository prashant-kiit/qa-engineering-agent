import { useEffect, useState } from "react";
import {
  apiUrl,
  authHeaders,
  type Cart,
  type Credentials,
} from "../api";

export type CartViewProps = {
  credentials: Credentials;
  onCheckout?: () => void;
};

/**
 * Cart view: fetches the current cart from `GET /cart` (Basic auth), lists each
 * line item with its quantity and the cart total, renders a clear empty state,
 * and exposes a proceed-to-checkout control.
 */
export function CartView({ credentials, onCheckout }: CartViewProps) {
  const [cart, setCart] = useState<Cart | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const res = await fetch(apiUrl("/cart"), {
          method: "GET",
          headers: authHeaders(credentials),
        });
        if (!res.ok) {
          if (active) setError("Failed to load cart.");
          return;
        }
        const data = (await res.json()) as Cart;
        if (active) setCart(data);
      } catch {
        if (active) setError("Failed to load cart.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [credentials]);

  const items = cart?.items ?? [];
  const isEmpty = !loading && items.length === 0;

  return (
    <section>
      <h1>Your cart</h1>
      {loading && <p>Loading cart…</p>}
      {error && <p role="alert">{error}</p>}
      {isEmpty && <p data-testid="cart-empty">Your cart is empty.</p>}
      {items.length > 0 && (
        <ul>
          {items.map((line, i) => (
            <li key={`${line.product_id}-${i}`} data-testid="cart-line">
              <span>Product #{line.product_id}</span>
              <span>Qty: {line.quantity}</span>
            </li>
          ))}
        </ul>
      )}
      {cart && (
        <p>
          Total: <span data-testid="cart-total">{cart.total}</span>
        </p>
      )}
      <button data-testid="cart-checkout" onClick={() => onCheckout?.()}>
        Proceed to checkout
      </button>
    </section>
  );
}
