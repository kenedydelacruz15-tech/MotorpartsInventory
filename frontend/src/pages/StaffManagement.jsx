import { useEffect, useState } from "react";
import api from "../services/api";

export default function StaffManagement() {
  const [staff, setStaff] = useState([]);

  const [showForm, setShowForm] = useState(false);
  const [editingStaff, setEditingStaff] = useState(null);

  const [form, setForm] = useState({
    full_name: "",
    username: "",
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // Load STAFF accounts from the owner's store
  const loadStaff = async () => {
    try {
      setLoading(true);
      setError("");

      const res = await api.get("/api/users/");

      const staffOnly = (res.data || []).filter(
        (user) => user.role === "STAFF"
      );

      setStaff(staffOnly);
    } catch (err) {
      console.error("Could not load staff:", err);

      setError(
        err.response?.data?.error ||
          "Could not load staff."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStaff();
  }, []);

  // Handle form fields
  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  // Reset the staff form
  const resetForm = () => {
    setForm({
      full_name: "",
      username: "",
      email: "",
      password: "",
    });

    setEditingStaff(null);
    setShowForm(false);
  };

  // Open Add Staff form
  const openAddForm = () => {
    setError("");
    setMessage("");
    setEditingStaff(null);

    setForm({
      full_name: "",
      username: "",
      email: "",
      password: "",
    });

    setShowForm(true);
  };

  // Add staff account
  const addStaff = async (e) => {
    e.preventDefault();

    setError("");
    setMessage("");

    if (!form.full_name.trim()) {
      setError("Full name is required.");
      return;
    }

    if (!form.username.trim()) {
      setError("Username is required.");
      return;
    }

    if (!form.email.trim()) {
      setError("Email is required.");
      return;
    }

    if (!form.password) {
      setError("Password is required.");
      return;
    }

    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    try {
      setSaving(true);

      await api.post("/api/users/", {
        full_name: form.full_name.trim(),
        username: form.username.trim(),
        email: form.email.trim(),
        password: form.password,
      });

      setMessage("Staff account created successfully.");

      resetForm();
      await loadStaff();
    } catch (err) {
      console.error("Could not create staff:", err);

      setError(
        err.response?.data?.error ||
          "Could not create staff account."
      );
    } finally {
      setSaving(false);
    }
  };

  // Start editing a staff account
  const startEdit = (user) => {
    setEditingStaff(user);

    setForm({
      full_name: user.full_name || "",
      username: user.username || "",
      email: user.email || "",
      password: "",
    });

    setShowForm(true);
    setMessage("");
    setError("");
  };

  // Update staff account
  const updateStaff = async (e) => {
    e.preventDefault();

    setError("");
    setMessage("");

    if (!form.full_name.trim()) {
      setError("Full name is required.");
      return;
    }

    if (!form.email.trim()) {
      setError("Email is required.");
      return;
    }

    try {
      setSaving(true);

      await api.put(
        `/api/users/${editingStaff.user_id}`,
        {
          full_name: form.full_name.trim(),
          email: form.email.trim(),
        }
      );

      setMessage("Staff information updated successfully.");

      resetForm();
      await loadStaff();
    } catch (err) {
      console.error("Could not update staff:", err);

      setError(
        err.response?.data?.error ||
          "Could not update staff information."
      );
    } finally {
      setSaving(false);
    }
  };

  // Activate or deactivate a staff account
  const toggleStatus = async (user) => {
    const action = user.is_active
      ? "deactivate"
      : "activate";

    const confirmed = window.confirm(
      `Are you sure you want to ${action} ${user.full_name}?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");
      setMessage("");

      await api.put(
        `/api/users/${user.user_id}/deactivate`
      );

      setMessage(
        user.is_active
          ? "Staff account deactivated."
          : "Staff account activated."
      );

      await loadStaff();
    } catch (err) {
      console.error("Could not change staff status:", err);

      setError(
        err.response?.data?.error ||
          "Could not change staff status."
      );
    }
  };

  return (
    <div className="staff-page">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1>Staff Management</h1>

          <p className="muted">
            Manage staff accounts for your store.
          </p>
        </div>

        {!showForm && (
          <button
            type="button"
            className="primary"
            onClick={openAddForm}
          >
            + Add Staff
          </button>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="alert">
          {error}
        </div>
      )}

      {/* Success message */}
      {message && (
        <div className="success">
          {message}
        </div>
      )}

      {/* Add/Edit staff form */}
      {showForm && (
        <div className="product-form-card">
          <h2>
            {editingStaff
              ? "Edit Staff"
              : "Add Staff"}
          </h2>

          <form
            onSubmit={
              editingStaff
                ? updateStaff
                : addStaff
            }
          >
            <label>Full Name</label>

            <input
              name="full_name"
              value={form.full_name}
              onChange={handleChange}
              placeholder="Enter full name"
              required
            />

            <label>Username</label>

            <input
              name="username"
              value={form.username}
              onChange={handleChange}
              placeholder="Enter username"
              disabled={!!editingStaff}
              required
            />

            <label>Email</label>

            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="Enter email"
              required
            />

            {!editingStaff && (
              <>
                <label>Password</label>

                <input
                  type="password"
                  name="password"
                  value={form.password}
                  onChange={handleChange}
                  placeholder="Minimum 8 characters"
                  required
                />
              </>
            )}

            <div className="form-actions">
              <button
                type="submit"
                className="primary"
                disabled={saving}
              >
                {saving
                  ? "Saving..."
                  : editingStaff
                  ? "Update Staff"
                  : "Create Staff"}
              </button>

              <button
                type="button"
                className="secondary"
                onClick={resetForm}
                disabled={saving}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Staff table */}
      <div className="staff-card">
        <div className="staff-header">
          <div>
            <h2>Staff Accounts</h2>

            <p>
              Staff accounts assigned to your store.
            </p>
          </div>
        </div>

        <div className="table-wrapper">
          {loading ? (
            <p className="muted staff-message">
              Loading staff...
            </p>
          ) : staff.length === 0 ? (
            <p className="muted staff-message">
              No staff accounts found.
            </p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Full Name</th>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {staff.map((user) => (
                  <tr key={user.user_id}>
                    <td>{user.full_name}</td>

                    <td>{user.username}</td>

                    <td>{user.email}</td>

                    <td>
                      {user.is_active ? (
                        <span className="staff-active">
                          Active
                        </span>
                      ) : (
                        <span className="staff-inactive">
                          Inactive
                        </span>
                      )}
                    </td>

                    <td>
                      {user.created_at
                        ? new Date(
                            user.created_at
                          ).toLocaleDateString()
                        : "-"}
                    </td>

                    <td>
                      <div className="staff-table-actions">
                        {/* Edit button */}
                        <button
                          type="button"
                          className="staff-edit-button"
                          onClick={() =>
                            startEdit(user)
                          }
                        >
                          Edit
                        </button>

                        {/* Activate / Deactivate button */}
                        <button
                          type="button"
                          className={
                            user.is_active
                              ? "staff-deactivate-button"
                              : "staff-restore-button"
                          }
                          onClick={() =>
                            toggleStatus(user)
                          }
                        >
                          {user.is_active
                            ? "Deactivate"
                            : "Activate"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}