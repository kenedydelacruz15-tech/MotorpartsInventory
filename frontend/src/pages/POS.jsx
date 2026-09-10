import { useEffect, useMemo, useState } from "react";
import api from "../services/api";

export default function POS() {
  const [products, setProducts] = useState([]);
  const [sales, setSales] = useState([]);

  const [query, setQuery] = useState("");
  const [cart, setCart] = useState([]);

  const [payment, setPayment] = useState("");
  const [method, setMethod] = useState("CASH");

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [loadingProducts, setLoadingProducts] = useState(false);
  const [loadingSales, setLoadingSales] = useState(false);
  const [voidingSale, setVoidingSale] = useState(null);

  const [userRole, setUserRole] = useState("");

  useEffect(() => {
    try {
      const user = JSON.parse(
        localStorage.getItem("user")
      );

      if (user?.role) {
        setUserRole(user.role.toUpperCase());
      }
    } catch (error) {
      console.error("Could not read user role.");
    }
  }, []);

  const loadProducts = async () => {
    try {
      setLoadingProducts(true);
      setError("");

      const res = await api.get("/api/inventory/");

      setProducts(
        Array.isArray(res.data)
          ? res.data
          : res.data.inventory || []
      );
    } catch (err) {
      setError(
        err.response?.data?.error ||
          err.response?.data?.message ||
          "Could not load products."
      );
    } finally {
      setLoadingProducts(false);
    }
  };

  const loadSales = async () => {
    try {
      setLoadingSales(true);
      setError("");

      const res = await api.get("/api/sales/");

      setSales(
        Array.isArray(res.data)
          ? res.data
          : res.data.sales || []
      );
    } catch (err) {
      setError(
        err.response?.data?.error ||
          err.response?.data?.message ||
          "Could not load sales."
      );
    } finally {
      setLoadingSales(false);
    }
  };

  useEffect(() => {
    loadProducts();
    loadSales();
  }, []);

  const filtered = products.filter((product) => {
    const q = query.toLowerCase().trim();

    return (
      (product.product_name || "")
        .toLowerCase()
        .includes(q) ||
      (product.sku || "")
        .toLowerCase()
        .includes(q)
    );
  });

  const addToCart = (product) => {
    setError("");
    setMessage("");

    const stock = Number(product.stock_quantity);

    if (stock <= 0) {
      setError("This product is out of stock.");
      return;
    }

    setCart((oldCart) => {
      const existing = oldCart.find(
        (item) => item.product_id === product.product_id
      );

      if (existing) {
        if (existing.quantity >= stock) {
          setError("You cannot add more than the available stock.");
          return oldCart;
        }

        return oldCart.map((item) =>
          item.product_id === product.product_id
            ? {
                ...item,
                quantity: item.quantity + 1,
              }
            : item
        );
      }

      return [
        ...oldCart,
        {
          product_id: product.product_id,
          product_name: product.product_name,
          sku: product.sku,
          part_number: product.part_number,
          selling_price: Number(product.selling_price),
          quantity: 1,
          stock_quantity: stock,
        },
      ];
    });
  };

  const updateQuantity = (productId, value) => {
    const quantity = Math.max(1, Number(value) || 1);

    setCart((oldCart) =>
      oldCart.map((item) =>
        item.product_id === productId
          ? {
              ...item,
              quantity: Math.min(
                quantity,
                item.stock_quantity
              ),
            }
          : item
      )
    );
  };

  const removeFromCart = (productId) => {
    setCart((oldCart) =>
      oldCart.filter(
        (item) => item.product_id !== productId
      )
    );
  };

  const clearCart = () => {
    setCart([]);
    setPayment("");
    setError("");
    setMessage("");
  };

  const total = useMemo(() => {
    return cart.reduce(
      (sum, item) =>
        sum + item.selling_price * item.quantity,
      0
    );
  }, [cart]);

  const change = Number(payment || 0) - total;

  // CREATE SALE
  const completeSale = async () => {
    setError("");
    setMessage("");

    if (cart.length === 0) {
      setError("Cart is empty.");
      return;
    }

    if (!payment || Number(payment) <= 0) {
      setError("Please enter the payment amount.");
      return;
    }

    if (Number(payment) < total) {
      setError("Payment is not enough.");
      return;
    }

    try {
      const res = await api.post("/api/sales/", {
        items: cart.map((item) => ({
          product_id: item.product_id,
          quantity: item.quantity,
        })),
        payment_amount: Number(payment),
        payment_method: method,
      });

      const sale = res.data.sale || res.data;

      setMessage(
        `Sale #${sale.sale_id} completed successfully. Change: ₱${Number(
          sale.change_amount ?? change
        ).toFixed(2)}`
      );

      setCart([]);
      setPayment("");
      setMethod("CASH");

      await loadProducts();
      await loadSales();
    } catch (err) {
      setError(
        err.response?.data?.error ||
          err.response?.data?.message ||
          "Could not complete sale."
      );
    }
  };

  // DELETE = VOID SALE
  const voidSale = async (sale) => {
    if (userRole !== "OWNER") {
      setError("Only the owner can void a sale.");
      return;
    }

    if (sale.status === "VOIDED") {
      setError("This sale has already been voided.");
      return;
    }

    const confirmed = window.confirm(
      `Void Sale #${sale.sale_id}?\n\n` +
        `This will restore the sold products to inventory.`
    );

    if (!confirmed) {
      return;
    }

    setError("");
    setMessage("");
    setVoidingSale(sale.sale_id);

    try {
      await api.put(
        `/api/sales/${sale.sale_id}/void`
      );

      setMessage(
        `Sale #${sale.sale_id} was voided successfully. Inventory has been restored.`
      );

      await loadProducts();
      await loadSales();
    } catch (err) {
      setError(
        err.response?.data?.error ||
          err.response?.data?.message ||
          "Could not void sale."
      );
    } finally {
      setVoidingSale(null);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>POS / Sales</h1>
          <p>
            Process sales and manage sales history.
          </p>
        </div>
      </div>

      {error && (
        <div className="alert">
          {error}
        </div>
      )}

      {message && (
        <div className="success">
          {message}
        </div>
      )}

      <div className="pos-layout">
        <section>
          <div className="product-form-card">
            <div className="form-header">
              <div>
                <h2>Products</h2>
                <p>
                  Select a product to add it to the cart.
                </p>
              </div>
            </div>

            <input
              className="search"
              type="text"
              placeholder="Search product or SKU..."
              value={query}
              onChange={(e) =>
                setQuery(e.target.value)
              }
            />

            {loadingProducts ? (
              <div className="empty-state">
                Loading products...
              </div>
            ) : filtered.length === 0 ? (
              <div className="empty-state">
                <h3>No products found</h3>
                <p>
                  No available products match your search.
                </p>
              </div>
            ) : (
              <div className="product-grid">
                {filtered.map((product) => (
                  <button
                    type="button"
                    className="product-card"
                    key={product.product_id}
                    onClick={() =>
                      addToCart(product)
                    }
                    disabled={
                      Number(product.stock_quantity) <= 0
                    }
                  >
                    <strong>
                      {product.product_name}
                    </strong>

                    <span>
                      SKU: {product.sku}
                    </span>

                    <span>
                      ₱
                      {Number(
                        product.selling_price
                      ).toFixed(2)}
                    </span>

                    <small>
                      Stock: {product.stock_quantity}
                    </small>
                  </button>
                ))}
              </div>
            )}
          </div>
        </section>

        <section>
          <div className="cart-card">
            <h2>Cart</h2>

            {cart.length === 0 ? (
              <p className="muted">
                No items added to cart.
              </p>
            ) : (
              cart.map((item) => (
                <div
                  className="cart-item"
                  key={item.product_id}
                >
                  <div>
                    <strong>
                      {item.product_name}
                    </strong>

                    <div className="muted">
                      ₱
                      {item.selling_price.toFixed(2)} each
                    </div>
                  </div>

                  <input
                    type="number"
                    min="1"
                    max={item.stock_quantity}
                    value={item.quantity}
                    onChange={(e) =>
                      updateQuantity(
                        item.product_id,
                        e.target.value
                      )
                    }
                  />

                  <strong>
                    ₱
                    {(
                      item.selling_price *
                      item.quantity
                    ).toFixed(2)}
                  </strong>

                  <button
                    type="button"
                    onClick={() =>
                      removeFromCart(item.product_id)
                    }
                  >
                    Remove
                  </button>
                </div>
              ))
            )}

            <hr />

            <div className="total">
              <span>Total</span>

              <strong>
                ₱{total.toFixed(2)}
              </strong>
            </div>

            <label>
              Payment Method
            </label>

            <select
              value={method}
              onChange={(e) =>
                setMethod(e.target.value)
              }
            >
              <option value="CASH">CASH</option>
              <option value="GCASH">GCASH</option>
              <option value="CARD">CARD</option>
            </select>

            <label>
              Payment Amount
            </label>

            <input
              type="number"
              min="0"
              step="0.01"
              placeholder="0.00"
              value={payment}
              onChange={(e) =>
                setPayment(e.target.value)
              }
            />

            <div className="change">
              Change: ₱
              {Math.max(0, change).toFixed(2)}
            </div>

            <button
              type="button"
              className="primary full"
              onClick={completeSale}
            >
              Complete Sale
            </button>

            {cart.length > 0 && (
              <button
                type="button"
                className="full"
                onClick={clearCart}
              >
                Clear Cart
              </button>
            )}
          </div>
        </section>
      </div>

      {/* READ SALES */}
      <div
        className="products-card"
        style={{ marginTop: "24px" }}
      >
        <div className="table-header">
          <div>
            <h2>Sales History</h2>

            <span>
              View completed and voided sales.
            </span>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Sale ID</th>
                <th>Cashier</th>
                <th>Total</th>
                <th>Payment</th>
                <th>Change</th>
                <th>Method</th>
                <th>Date</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {loadingSales ? (
                <tr>
                  <td
                    colSpan="9"
                    className="empty-state"
                  >
                    Loading sales...
                  </td>
                </tr>
              ) : sales.length === 0 ? (
                <tr>
                  <td
                    colSpan="9"
                    className="empty-state"
                  >
                    <h3>No sales yet</h3>

                    <p>
                      Completed sales will appear here.
                    </p>
                  </td>
                </tr>
              ) : (
                sales.map((sale) => (
                  <tr key={sale.sale_id}>
                    <td>
                      #{sale.sale_id}
                    </td>

                    <td>
                      {sale.cashier || "-"}
                    </td>

                    <td>
                      ₱
                      {Number(
                        sale.total_sales
                      ).toFixed(2)}
                    </td>

                    <td>
                      ₱
                      {Number(
                        sale.payment_amount
                      ).toFixed(2)}
                    </td>

                    <td>
                      ₱
                      {Number(
                        sale.change_amount
                      ).toFixed(2)}
                    </td>

                    <td>
                      {sale.payment_method}
                    </td>

                    <td>
                      {sale.sale_date
                        ? new Date(
                            sale.sale_date
                          ).toLocaleString()
                        : "-"}
                    </td>

                    <td>
                      {sale.status === "VOIDED" ? (
                        <span className="status-badge inactive">
                          Voided
                        </span>
                      ) : (
                        <span className="status-badge active">
                          Completed
                        </span>
                      )}
                    </td>

                    <td>
                      {userRole === "OWNER" &&
                      sale.status !== "VOIDED" ? (
                        <button
                          type="button"
                          className="action-button deactivate-button"
                          onClick={() =>
                            voidSale(sale)
                          }
                          disabled={
                            voidingSale === sale.sale_id
                          }
                        >
                          {voidingSale === sale.sale_id
                            ? "Voiding..."
                            : "Void Sale"}
                        </button>
                      ) : sale.status === "VOIDED" ? (
                        <span className="muted">
                          No action
                        </span>
                      ) : (
                        <span className="muted">
                          Owner only
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}