import { useEffect, useState } from "react";
import api from "../services/api";
import { getRole, getUser } from "../services/auth";

export default function StoreSettings() {
  const user = getUser();
  const role = getRole();

  const [store, setStore] = useState({
    store_name: "",
    address: "",
    contact_number: "",
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (role !== "OWNER") {
      setLoading(false);
      return;
    }

    loadStore();
  }, [role]);

  const loadStore = async () => {
    try {
      setLoading(true);
      setError("");

      const res = await api.get("/api/store/profile");

      setStore({
        store_name: res.data?.store_name || "",
        address: res.data?.address || "",
        contact_number: res.data?.contact_number || "",
      });
    } catch (err) {
      console.error("Could not load store information:", err);

      setError(
        err.response?.data?.error ||
          "Could not load store information."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setStore({
      ...store,
      [e.target.name]: e.target.value,
    });
  };

  const saveStore = async (e) => {
    e.preventDefault();

    setError("");
    setMessage("");

    if (!store.store_name.trim()) {
      setError("Store name is required.");
      return;
    }

    try {
      setSaving(true);

      await api.put("/api/store/profile", {
        store_name: store.store_name.trim(),
        address: store.address.trim(),
        contact_number: store.contact_number.trim(),
      });

      setMessage(
        "Store information updated successfully."
      );
    } catch (err) {
      console.error("Could not update store information:", err);

      setError(
        err.response?.data?.error ||
          "Could not update store information."
      );
    } finally {
      setSaving(false);
    }
  };

  if (role !== "OWNER") {
    return (
      <div>
        <h1>Store Settings</h1>

        <div className="alert">
          Only the store owner can access store settings.
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div>
        <h1>Store Settings</h1>

        <p className="muted">
          Loading store information...
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Store Settings</h1>

          <p className="muted">
            Manage your store information and setup details.
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

      <div className="product-form-card">
        <h2>Store Information</h2>

        <p className="muted">
          Store owner:{" "}
          <strong>
            {user?.full_name || user?.username}
          </strong>
        </p>

        <form onSubmit={saveStore}>
          <label>Store Name</label>

          <input
            name="store_name"
            value={store.store_name}
            onChange={handleChange}
            placeholder="Enter store name"
            required
          />

          <label>Address</label>

          <input
            name="address"
            value={store.address}
            onChange={handleChange}
            placeholder="Enter store address"
          />

          <label>Contact Number</label>

          <input
            name="contact_number"
            value={store.contact_number}
            onChange={handleChange}
            placeholder="Enter contact number"
          />

          <button
            type="submit"
            className="primary"
            disabled={saving}
          >
            {saving
              ? "Saving..."
              : "Save Store Information"}
          </button>
        </form>
      </div>
    </div>
  );
}