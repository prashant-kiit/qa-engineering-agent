import type { Order } from "../api";

export type OrderConfirmationViewProps = {
  order: Order;
};

/**
 * Order-confirmation view: renders the created order's id and total.
 */
export function OrderConfirmationView({ order }: OrderConfirmationViewProps) {
  return (
    <section>
      <h1>Order confirmed</h1>
      <p>
        Order id: <span data-testid="order-id">{order.id}</span>
      </p>
      <p>
        Order total: <span data-testid="order-total">{order.total}</span>
      </p>
    </section>
  );
}
