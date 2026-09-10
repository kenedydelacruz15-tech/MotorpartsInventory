import { useEffect, useMemo, useState } from "react";
import api from "../services/api";

export default function Inventory() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  const [editingItem, setEditingItem] = useState(null);
  const [stockQuantity, setStockQuantity] = useState("");
  const [saving, setSaving] = useState(false);

  const [message, setMessage] = useState("");

  const loadInventory = async () => {
    try {
      setLoading(true);
      setError("");

      const res = await api.get("/api/inventory/");

      setItems(
        Array.isArray(res.data)
          ? res.data
          : res.data.inventory || []
      );
    } catch (err) {
      setError(
        err.response?.data?.error ||
          err.response?.data?.message ||
          "Could not load inventory."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInventory();
  }, []);

  const filteredItems = useMemo(() => {
    const value = search.toLowerCase().trim();

    if (!value) {
      return items;
    }

    return items.filter(
      (item) =>
        (item.product_name || "")
          .toLowerCase()
          .includes(value) ||
        (item.sku || "")
          .toLowerCase()
          .includes(value) ||
        (item.brand || "")
          .toLowerCase()
          .includes(value) ||
        (item.category_name || "")
          .toLowerCase()
          .includes(value)
    );
  }, [items, search]);

  const groupedByCategory = useMemo(() => {
    return filteredItems.reduce((groups, item) => {
      const category =
        item.category_name || "Uncategorized";

      if (!groups[category]) {
        groups[category] = [];
      }

      groups[category].push(item);

      return groups;
    }, {});
  }, [filteredItems]);

  const openEdit = (item) => {
    setEditingItem(item);
    setStockQuantity(item.stock_quantity ?? "");
    setError("");
    setMessage("");
  };

  const closeEdit = () => {
    setEditingItem(null);
    setStockQuantity("");
  };

  const updateStock = async (e) => {
    e.preventDefault();

    if (stockQuantity === "") {
      setError("Stock quantity is required.");
      return;
    }

    if (Number(stockQuantity) < 0) {
      setError("Stock quantity cannot be negative.");
      return;
    }

    try {
      setSaving(true);
      setError("");
      setMessage("");

      await api.put(
        `/api/inventory/${editingItem.inventory_id}`,
        {
          stock_quantity: Number(stockQuantity),
        }
      );

      closeEdit();
      setMessage("Inventory stock updated successfully.");
      await loadInventory();
    } catch (err) {
      setError(
        err.response?.data?.error ||
          err.response?.data?.message ||
          "Could not update inventory."
      );
    } finally {
      setSaving(false);
    }
  };

  const deactivateInventory = async (item) => {
    const stock = Number(item.stock_quantity) || 0;

    if (stock > 0) {
      setError(
        "Inventory cannot be deactivated while stock is greater than 0."
      );
      return;
    }

    const confirmed = window.confirm(
      `Deactivate inventory for "${item.product_name}"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");
      setMessage("");

      await api.put(
        `/api/inventory/${item.inventory_id}/deactivate`
      );

      setMessage("Inventory deactivated successfully.");
      await loadInventory();
    } catch (err) {
      setError(
        err.response?.data?.error ||
          err.response?.data?.message ||
          "Could not deactivate inventory."
      );
    }
  };

  const restoreInventory = async (item) => {
    const confirmed = window.confirm(
      `Restore inventory for "${item.product_name}"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");
      setMessage("");

      await api.put(
        `/api/inventory/${item.inventory_id}/restore`
      );

      setMessage("Inventory restored successfully.");
      await loadInventory();
    } catch (err) {
      setError(
        err.response?.data?.error ||
          err.response?.data?.message ||
          "Could not restore inventory."
      );
    }
  };

  const categories = Object.entries(groupedByCategory);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Current Inventory</h1>
          <p>
            View and manage current stock levels by category.
          </p>
        </div>
      </div>

      {error && <div className="alert">{error}</div>}

      {message && (
        <div className="alert success-alert">
          {message}
        </div>
      )}

      <div className="products-card">
        <div className="table-header">
          <div>
            <h2>Inventory</h2>
            <span>
              {items.length} product
              {items.length !== 1 ? "s" : ""}
            </span>
          </div>

          <input
            className="search"
            type="text"
            placeholder="Search product, SKU, brand, or category..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {loading ? (
          <div className="empty-state">
            Loading inventory...
          </div>
        ) : categories.length === 0 ? (
          <div className="empty-state">
            <h3>No inventory found</h3>
            <p>
              There are no inventory products to display.
            </p>
          </div>
        ) : (
          <div className="inventory-categories">
            {categories.map(
              ([categoryName, products]) => (
                <div
                  className="inventory-category"
                  key={categoryName}
                >
                  <div className="inventory-category-header">
                    <div>
                      <h3>{categoryName}</h3>
                      <span>
                        {products.length} product
                        {products.length !== 1
                          ? "s"
                          : ""}
                      </span>
                    </div>
                  </div>

                  <div className="table-container">
                    <table>
                      <thead>
                        <tr>
                          <th>Product</th>
                          <th>SKU</th>
                          <th>Brand</th>
                          <th>Price</th>
                          <th>Stock</th>
                          <th>Reorder Level</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>

                      <tbody>
                        {products.map((item) => {
                          const stock =
                            Number(item.stock_quantity) || 0;

                          const reorderLevel =
                            Number(item.reorder_level) || 0;

                          const isLowStock =
                            stock <= reorderLevel;

                          return (
                            <tr
                              key={
                                item.inventory_id ||
                                item.product_id
                              }
                            >
                              <td>
                                <strong>
                                  {item.product_name}
                                </strong>
                              </td>

                              <td>
                                {item.sku || "-"}
                              </td>

                              <td>
                                {item.brand || "-"}
                              </td>

                              <td>
                                ₱
                                {Number(
                                  item.selling_price || 0
                                ).toFixed(2)}
                              </td>

                              <td
                                className={
                                  isLowStock
                                    ? "low-stock"
                                    : ""
                                }
                              >
                                {stock}
                              </td>

                              <td>
                                {reorderLevel}
                              </td>

                              <td>
                                {item.is_active === 0 ||
                                item.is_active === false ? (
                                  <span className="status-badge inactive">
                                    Inactive
                                  </span>
                                ) : stock === 0 ? (
                                  <span className="status-badge inactive">
                                    Out of Stock
                                  </span>
                                ) : isLowStock ? (
                                  <span className="status-badge inactive">
                                    Reorder
                                  </span>
                                ) : (
                                  <span className="status-badge active">
                                    Good Stock
                                  </span>
                                )}
                              </td>

                              <td>
                                <div className="action-buttons">
                                  <button
                                    type="button"
                                    className="btn btn-secondary"
                                    onClick={() =>
                                      openEdit(item)
                                    }
                                    disabled={
                                      item.is_active === 0 ||
                                      item.is_active === false
                                    }
                                  >
                                    Edit
                                  </button>

                                  {item.is_active === 0 ||
                                  item.is_active === false ? (
                                    <button
                                      type="button"
                                      className="btn btn-primary"
                                      onClick={() =>
                                        restoreInventory(item)
                                      }
                                    >
                                      Restore
                                    </button>
                                  ) : (
                                    <button
                                      type="button"
                                      className="btn btn-danger"
                                      onClick={() =>
                                        deactivateInventory(
                                          item
                                        )
                                      }
                                    >
                                      Deactivate
                                    </button>
                                  )}
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )
            )}
          </div>
        )}
      </div>

      {editingItem && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <div>
                <h2>Update Inventory</h2>
                <p>
                  {editingItem.product_name}
                </p>
              </div>

              <button
                type="button"
                className="modal-close"
                onClick={closeEdit}
              >
                ×
              </button>
            </div>

            <form onSubmit={updateStock}>
              <div className="form-group">
                <label>Product</label>
                <input
                  type="text"
                  value={
                    editingItem.product_name || ""
                  }
                  disabled
                />
              </div>

              <div className="form-group">
                <label>Current Stock</label>
                <input
                  type="number"
                  min="0"
                  value={stockQuantity}
                  onChange={(e) =>
                    setStockQuantity(e.target.value)
                  }
                  required
                />
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={closeEdit}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={saving}
                >
                  {saving
                    ? "Saving..."
                    : "Update Stock"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}