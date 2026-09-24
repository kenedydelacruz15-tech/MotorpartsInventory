import { useEffect, useState } from "react";
import api from "../services/api";

export default function Inventory() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Search
  const [search, setSearch] = useState("");

  // Stock movement modal
  const [movementItem, setMovementItem] = useState(null);
  const [movementType, setMovementType] = useState("");
  const [movementQuantity, setMovementQuantity] = useState("");
  const [movementReason, setMovementReason] = useState("");
  const [movementRemarks, setMovementRemarks] = useState("");

  // Adjust stock modal
  const [editItem, setEditItem] = useState(null);
  const [editQuantity, setEditQuantity] = useState("");

  // Load inventory
  const loadInventory = async () => {
    try {
      setLoading(true);
      setError("");

      const res = await api.get("/api/inventory/", {
        params: search ? { search } : {},
      });

      setItems(res.data || []);
    } catch (err) {
      console.error("Inventory load error:", err);
      setError(
        err.response?.data?.message ||
          err.response?.data?.error ||
          "Failed to load inventory."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInventory();
  }, []);

  // Search when user presses Enter
  const handleSearch = (e) => {
    e.preventDefault();
    loadInventory();
  };

  // Open Stock In / Stock Out modal
  const openMovement = (item, type) => {
    console.log("BUTTON CLICKED:", type, item);

    setMovementItem(item);
    setMovementType(type);
    setMovementQuantity("");
    setMovementReason("");
    setMovementRemarks("");
  };

  // Close movement modal
  const closeMovement = () => {
    setMovementItem(null);
    setMovementType("");
    setMovementQuantity("");
    setMovementReason("");
    setMovementRemarks("");
  };

  // Submit Stock In / Stock Out
  const submitMovement = async () => {
    if (!movementItem) return;

    const quantity = Number(movementQuantity);

    if (!quantity || quantity <= 0) {
      alert("Please enter a valid quantity.");
      return;
    }

    if (movementType === "STOCK_OUT" && !movementReason) {
      alert("Please select a reason for Stock Out.");
      return;
    }

    try {
      setLoading(true);

      const endpoint =
        movementType === "STOCK_IN"
          ? `/api/inventory/${movementItem.inventory_id}/stock-in`
          : `/api/inventory/${movementItem.inventory_id}/stock-out`;

      const payload = {
        quantity,
        remarks: movementRemarks,
      };

      if (movementType === "STOCK_IN") {
        payload.reference_type = "SUPPLIER";
      } else {
        payload.reference_type = movementReason;
      }

      await api.post(endpoint, payload);

      alert(
        movementType === "STOCK_IN"
          ? "Stock added successfully."
          : "Stock removed successfully."
      );

      closeMovement();
      await loadInventory();
    } catch (err) {
      console.error("Stock movement error:", err);

      alert(
        err.response?.data?.message ||
          err.response?.data?.error ||
          "Stock movement failed."
      );
    } finally {
      setLoading(false);
    }
  };

  // Open Adjust Stock modal
  const openEdit = (item) => {
    setEditItem(item);
    setEditQuantity(item.stock_quantity);
  };

  // Close Adjust Stock modal
  const closeEdit = () => {
    setEditItem(null);
    setEditQuantity("");
  };

  // Adjust stock
  const submitEdit = async () => {
    if (!editItem) return;

    const quantity = Number(editQuantity);

    if (Number.isNaN(quantity) || quantity < 0) {
      alert("Please enter a valid stock quantity.");
      return;
    }

    try {
      setLoading(true);

      await api.put(`/api/inventory/${editItem.inventory_id}`, {
        stock_quantity: quantity,
      });

      alert("Stock adjusted successfully.");

      closeEdit();
      await loadInventory();
    } catch (err) {
      console.error("Stock adjustment error:", err);

      alert(
        err.response?.data?.message ||
          err.response?.data?.error ||
          "Stock adjustment failed."
      );
    } finally {
      setLoading(false);
    }
  };

  // Deactivate inventory
  const deactivateItem = async (item) => {
    if (Number(item.stock_quantity) !== 0) {
      alert("You can only deactivate an item when its stock is 0.");
      return;
    }

    const confirmed = window.confirm(
      `Deactivate "${item.product_name}"?`
    );

    if (!confirmed) return;

    try {
      setLoading(true);

      await api.put(
        `/api/inventory/${item.inventory_id}/deactivate`
      );

      alert("Inventory item deactivated.");

      await loadInventory();
    } catch (err) {
      console.error("Deactivate error:", err);

      alert(
        err.response?.data?.message ||
          err.response?.data?.error ||
          "Failed to deactivate item."
      );
    } finally {
      setLoading(false);
    }
  };

  // Restore inventory
  const restoreItem = async (item) => {
    const confirmed = window.confirm(
      `Restore "${item.product_name}"?`
    );

    if (!confirmed) return;

    try {
      setLoading(true);

      await api.put(
        `/api/inventory/${item.inventory_id}/restore`
      );

      alert("Inventory item restored.");

      await loadInventory();
    } catch (err) {
      console.error("Restore error:", err);

      alert(
        err.response?.data?.message ||
          err.response?.data?.error ||
          "Failed to restore item."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Inventory</h1>
          <p>Manage stock levels and inventory movements.</p>
        </div>
      </div>

      {/* Search */}
      <form className="search-bar" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search product, SKU, part number, brand..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        <button type="submit">
          Search
        </button>

        <button
          type="button"
          onClick={() => {
            setSearch("");
            setTimeout(loadInventory, 0);
          }}
        >
          Clear
        </button>
      </form>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {loading && (
        <div className="loading-message">
          Loading...
        </div>
      )}

      {/* Inventory table */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>SKU</th>
              <th>Part Number</th>
              <th>Brand</th>
              <th>Category</th>
              <th>Price</th>
              <th>Reorder Level</th>
              <th>Stock</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan="10" className="empty-state">
                  No inventory found.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.inventory_id}>
                  <td>
                    <strong>{item.product_name}</strong>
                  </td>

                  <td>
                    {item.sku || "-"}
                  </td>

                  <td>
                    {item.part_number || "-"}
                  </td>

                  <td>
                    {item.brand || "-"}
                  </td>

                  <td>
                    {item.category_name || "-"}
                  </td>

                  <td>
                    ₱{Number(item.selling_price || 0).toFixed(2)}
                  </td>

                  <td>
                    {item.reorder_level ?? 0}
                  </td>

                  <td>
                    <strong>
                      {item.stock_quantity}
                    </strong>
                  </td>

                  <td>
                    {item.is_active ? (
                      item.stock_quantity === 0 ? (
                        <span className="status-badge danger">
                          Out of Stock
                        </span>
                      ) : item.stock_quantity <=
                        Number(item.reorder_level || 0) ? (
                        <span className="status-badge warning">
                          Low Stock
                        </span>
                      ) : (
                        <span className="status-badge success">
                          In Stock
                        </span>
                      )
                    ) : (
                      <span className="status-badge">
                        Inactive
                      </span>
                    )}
                  </td>

                  <td>
                    <div className="action-buttons">
                      {item.is_active ? (
                        <>
                          {/* Stock In */}
                          <button
                            type="button"
                            className="btn-success"
                            onClick={() =>
                              openMovement(item, "STOCK_IN")
                            }
                          >
                            Stock In
                          </button>

                          {/* Stock Out */}
                          <button
                            type="button"
                            className="btn-warning"
                            onClick={() =>
                              openMovement(item, "STOCK_OUT")
                            }
                          >
                            Stock Out
                          </button>

                          {/* Adjust */}
                          <button
                            type="button"
                            className="btn-primary"
                            onClick={() => openEdit(item)}
                          >
                            Adjust
                          </button>

                          {/* Deactivate */}
                          <button
                            type="button"
                            className="btn-danger"
                            onClick={() =>
                              deactivateItem(item)
                            }
                          >
                            Deactivate
                          </button>
                        </>
                      ) : (
                        /* Restore */
                        <button
                          type="button"
                          className="btn-primary"
                          onClick={() =>
                            restoreItem(item)
                          }
                        >
                          Restore
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ============================= */}
      {/* STOCK IN / STOCK OUT MODAL */}
      {/* ============================= */}

      {movementItem && (
        <div
          className="inventory-modal-overlay"
          onClick={closeMovement}
        >
          <div
            className="inventory-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <h2>
              {movementType === "STOCK_IN"
                ? "Stock In"
                : "Stock Out"}
            </h2>

            <div className="modal-product">
              <strong>
                {movementItem.product_name}
              </strong>

              <span>
                Current Stock:{" "}
                {movementItem.stock_quantity}
              </span>
            </div>

            <label>
              Quantity
            </label>

            <input
              type="number"
              min="1"
              placeholder="Enter quantity"
              value={movementQuantity}
              onChange={(e) =>
                setMovementQuantity(e.target.value)
              }
              autoFocus
            />

            {movementType === "STOCK_OUT" && (
              <>
                <label>
                  Reason
                </label>

                <select
                  value={movementReason}
                  onChange={(e) =>
                    setMovementReason(e.target.value)
                  }
                >
                  <option value="">
                    Select reason
                  </option>

                  <option value="DAMAGED">
                    Damaged
                  </option>

                  <option value="LOST">
                    Lost
                  </option>

                  <option value="ADJUSTMENT">
                    Adjustment
                  </option>

                  <option value="OTHER">
                    Other
                  </option>
                </select>
              </>
            )}

            <label>
              Remarks
            </label>

            <textarea
              placeholder="Optional remarks..."
              value={movementRemarks}
              onChange={(e) =>
                setMovementRemarks(e.target.value)
              }
            />

            <div className="modal-actions">
              <button
                type="button"
                onClick={closeMovement}
              >
                Cancel
              </button>

              <button
                type="button"
                className={
                  movementType === "STOCK_IN"
                    ? "btn-success"
                    : "btn-warning"
                }
                onClick={submitMovement}
                disabled={loading}
              >
                {loading
                  ? "Processing..."
                  : "Confirm"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================= */}
      {/* ADJUST STOCK MODAL */}
      {/* ============================= */}

      {editItem && (
        <div
          className="inventory-modal-overlay"
          onClick={closeEdit}
        >
          <div
            className="inventory-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <h2>
              Adjust Stock
            </h2>

            <div className="inventory-modal-product">
              <strong>
                {editItem.product_name}
              </strong>

              <span>
                Current Stock:{" "}
                {editItem.stock_quantity}
              </span>
            </div>

            <p className="modal-help">
              Use Adjust only when the actual physical
              stock does not match the system stock.
            </p>

            <label>
              New Stock Quantity
            </label>

            <input
              type="number"
              min="0"
              value={editQuantity}
              onChange={(e) =>
                setEditQuantity(e.target.value)
              }
              autoFocus
            />

            <div className="modal-actions">
              <button
                type="button"
                onClick={closeEdit}
              >
                Cancel
              </button>

              <button
                type="button"
                className="btn-primary"
                onClick={submitEdit}
                disabled={loading}
              >
                {loading
                  ? "Saving..."
                  : "Save Adjustment"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}