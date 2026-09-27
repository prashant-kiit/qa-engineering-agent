import { useEffect, useState } from "react";
import {
  apiUrl,
  authHeaders,
  type Credentials,
  type Product,
} from "../api";

export type ProductListViewProps = {
  credentials: Credentials;
};

/**
 * Product list view: fetches the catalog from `GET /products` (Basic auth) and
 * renders one entry per product with an add-to-cart control that issues
 * `POST /cart/items { product_id, quantity }`. A running cart count reflects
 * successful adds.
 */
export function ProductListView({ credentials }: ProductListViewProps) {
  const [products, setProducts] = useState<Product[]>([]);
  const [cartCount, setCartCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const res = await fetch(apiUrl("/products"), {
          method: "GET",
          headers: authHeaders(credentials),
        });
        if (!res.ok) {
          if (active) setError("Failed to load products.");
          return;
        }
        const data = (await res.json()) as Product[];
        if (active) setProducts(data);
      } catch {
        if (active) setError("Failed to load products.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [credentials]);

  async function addToCart(product: Product) {
    try {
      const res = await fetch(apiUrl("/cart/items"), {
        method: "POST",
        headers: authHeaders(credentials),
        body: JSON.stringify({ product_id: product.id, quantity: 1 }),
      });
      if (res.ok) {
        setCartCount((c) => c + 1);
      } else {
        setError("Failed to add item to cart.");
      }
    } catch {
      setError("Failed to add item to cart.");
    }
  }

  return (
    <section>
      <header>
        <h1>Products</h1>
        <span data-testid="cart-count">{cartCount}</span>
      </header>
      {loading && <p>Loading products…</p>}
      {error && <p role="alert">{error}</p>}
      <ul>
        {products.map((p) => (
          <li key={p.id} data-testid="product-item">
            <span>{p.name}</span>
            <span>{p.price}</span>
            <button data-testid="add-to-cart" onClick={() => addToCart(p)}>
              Add to cart
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
