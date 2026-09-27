import { useState } from "react";
import {
  LoginView,
  ProductListView,
  CartView,
  CheckoutView,
} from "./views";
import type { Credentials } from "./api";

type Screen = "products" | "cart" | "checkout";

/**
 * Minimal SPA wiring the five views into a login-gated shop flow. Views own all
 * backend calls; this component only holds the captured credentials and the
 * current screen.
 */
export default function App() {
  const [credentials, setCredentials] = useState<Credentials | null>(null);
  const [screen, setScreen] = useState<Screen>("products");

  if (!credentials) {
    return <LoginView onLogin={setCredentials} />;
  }

  return (
    <main>
      <nav>
        <button onClick={() => setScreen("products")}>Products</button>
        <button onClick={() => setScreen("cart")}>Cart</button>
        <button onClick={() => setScreen("checkout")}>Checkout</button>
      </nav>
      {screen === "products" && <ProductListView credentials={credentials} />}
      {screen === "cart" && (
        <CartView
          credentials={credentials}
          onCheckout={() => setScreen("checkout")}
        />
      )}
      {screen === "checkout" && <CheckoutView credentials={credentials} />}
    </main>
  );
}
