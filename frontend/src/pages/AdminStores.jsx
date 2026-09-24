import { useEffect, useState } from "react";
import api from "../services/api";

const emptyForm = {
  store_name: "",
  store_address: "",
  store_contact: "",
};

export default function AdminStores() {
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingStore, setEditingStore] = useState(null);

  const [form, setForm] = useState(emptyForm);

  useEffect(() => {
    loadStores();
  }, []);

  const loadStores = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/api/store");

      setStores(response.data);
    } catch (error) {
      console.error("Could not load stores:", error);

      setError(
        error.response?.data?.error ||
          "Could not load store information."
      );
    } finally {
      setLoading(false);
    }
  };

  const openCreateForm = () => {
    setEditingStore(null);
    setForm(emptyForm);
    setError("");
    setMessage("");
    setShowForm(true);
  };

  const openEditForm = (store) => {
    setEditingStore(store);

    setForm({
      store_name: store.store_name || "",
      store_address: store.store_address || "",
      store_contact: store.store_contact || "",
    });

    setError("");
    setMessage("");
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditingStore(null);
    setForm(emptyForm);
  };

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const saveStore = async (e) => {
    e.preventDefault();

    setError("");
    setMessage("");

    if (!form.store_name.trim()) {
      setError("Store name is required.");
      return;
    }

    try {
      setSaving(true);

      const payload = {
        store_name: form.store_name.trim(),
        store_address: form.store_address.trim(),
        store_contact: form.store_contact.trim(),
      };

      if (editingStore) {
        await api.put(
          `/api/store/${editingStore.store_id}`,
          payload
        );

        setMessage("Store updated successfully.");
      } else {
        await api.post("/api/store", payload);

        setMessage("Store created successfully.");
      }

      closeForm();
      await loadStores();
    } catch (error) {
      console.error("Could not save store:", error);

      setError(
        error.response?.data?.error ||
          "Could not save store."
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1>Stores</h1>

          <p className="muted">
            Create and manage registered stores.
          </p>
        </div>

        <div className="action-buttons">
          <button
            className="btn btn-primary"
            onClick={openCreateForm}
          >
            + Add Store
          </button>

          <button
            className="btn btn-secondary"
            onClick={loadStores}
            disabled={loading}
          >
            Refresh
          </button>
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

      {/* Create / Edit Store */}
      {showForm && (
        <div className="product-form-card">
          <div className="form-header">
            <div>
              <h2>
                {editingStore
                  ? "Edit Store"
                  : "Create Store"}
              </h2>

              <p>
                {editingStore
                  ? "Update the store information."
                  : "Create a new store for the system."}
              </p>
            </div>
          </div>

          <form onSubmit={saveStore}>
            <div className="form-grid">
              <div className="form-group">
                <label>Store Name</label>

                <input
                  name="store_name"
                  value={form.store_name}
                  onChange={handleChange}
                  placeholder="Enter store name"
                  required
                />
              </div>

              <div className="form-group">
                <label>Contact Number</label>

                <input
                  name="store_contact"
                  value={form.store_contact}
                  onChange={handleChange}
                  placeholder="Enter contact number"
                />
              </div>

              <div className="form-group form-group-full">
                <label>Address</label>

                <input
                  name="store_address"
                  value={form.store_address}
                  onChange={handleChange}
                  placeholder="Enter store address"
                />
              </div>

              <div className="product-form-buttons">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={saving}
                >
                  {saving
                    ? "Saving..."
                    : editingStore
                    ? "Update Store"
                    : "Create Store"}
                </button>

                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={closeForm}
                  disabled={saving}
                >
                  Cancel
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Store statistics */}
      <div className="dashboard-stats">
        <div className="stat-card">
          <span className="stat-label">
            Total Stores
          </span>

          <strong>
            {loading ? "..." : stores.length}
          </strong>

          <small>Registered stores</small>
        </div>

        <div className="stat-card">
          <span className="stat-label">
            Store Owners
          </span>

          <strong>
            {loading
              ? "..."
              : stores.filter(
                  (store) => store.owner_name
                ).length}
          </strong>

          <small>Stores with owners</small>
        </div>

        <div className="stat-card">
          <span className="stat-label">
            Store Staff
          </span>

          <strong>
            {loading
              ? "..."
              : stores.reduce(
                  (total, store) =>
                    total +
                    Number(store.staff_count || 0),
                  0
                )}
          </strong>

          <small>Total staff accounts</small>
        </div>
      </div>

      {/* Store table */}
      <div className="dashboard-section">
        <div className="section-header">
          <div>
            <h2>Registered Stores</h2>

            <p className="muted">
              Store information and assigned users.
            </p>
          </div>
        </div>

        {loading ? (
          <p className="muted">
            Loading stores...
          </p>
        ) : stores.length === 0 ? (
          <div className="info-panel">
            <strong>No stores found</strong>

            <p className="muted">
              There are currently no registered stores.
            </p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Store</th>
                  <th>Address</th>
                  <th>Contact</th>
                  <th>Owner</th>
                  <th>Staff</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {stores.map((store) => (
                  <tr key={store.store_id}>
                    <td>
                      <strong>
                        {store.store_name}
                      </strong>
                    </td>

                    <td>
                      {store.store_address ||
                        "Not provided"}
                    </td>

                    <td>
                      {store.store_contact ||
                        "Not provided"}
                    </td>

                    <td>
                      {store.owner_name ||
                        "No owner assigned"}
                    </td>

                    <td>
                      {store.staff_count || 0}
                    </td>

                    <td>
                      <div className="action-buttons">
                        <button
                          className="action-button edit-button"
                          onClick={() =>
                            openEditForm(store)
                          }
                        >
                          Edit
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}