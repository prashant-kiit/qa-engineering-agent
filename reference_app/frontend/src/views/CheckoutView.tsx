import { useState } from "react";
import {
  apiUrl,
  authHeaders,
  type Credentials,
  type Order,
} from "../api";
import { OrderConfirmationView } from "./OrderConfirmationView";

export type CheckoutViewProps = {
  credentials: Credentials;
};

/**
 * Checkout view: activating checkout issues `POST /checkout` (Basic auth). On
 * success it renders the order-confirmation with the returned order id + total;
 * on a client error it surfaces an error and shows no fabricated order.
 */
export function CheckoutView({ credentials }: CheckoutViewProps) {
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleCheckout() {
    setError(null);
    setBusy(true);
    try {
      const res = await fetch(apiUrl("/checkout"), {
        method: "POST",
        headers: authHeaders(credentials),
      });
      if (!res.ok) {
        setError("Checkout failed. Please review your cart and try again.");
        return;
      }
      const created = (await res.json()) as Order;
      setOrder(created);
    } catch {
      setError("Checkout failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  if (order) {
    return <OrderConfirmationView order={order} />;
  }

  return (
    <section>
      <h1>Checkout</h1>
      <button data-testid="checkout-submit" onClick={handleCheckout} disabled={busy}>
        Place order
      </button>
      {error && (
        <p data-testid="checkout-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
