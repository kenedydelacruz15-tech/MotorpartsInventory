import { useEffect, useState } from "react";
import api from "../services/api";

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [stores, setStores] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);

  const [form, setForm] = useState({
    full_name: "",
    username: "",
    email: "",
    password: "",
    role: "STAFF",
    store_id: ""
  });

  useEffect(() => {
    loadUsers();
    loadStores();
  }, []);

  const loadUsers = async () => {
    try {
      setError("");

      const res = await api.get("/api/users/admin/users");

      setUsers(res.data);
    } catch (error) {
      console.error("Could not load users:", error);

      setError(
        error.response?.data?.error ||
        "Could not load users."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadStores = async () => {
    try {
      // Temporary store loading endpoint.
      const res = await api.get("/api/store");

      setStores(res.data);
    } catch (error) {
      console.error("Could not load stores:", error);
    }
  };

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setError("");

      await api.post(
        "/api/users/admin/users",
        {
          ...form,
          store_id: Number(form.store_id)
        }
      );

      setForm({
        full_name: "",
        username: "",
        email: "",
        password: "",
        role: "STAFF",
        store_id: ""
      });

      setShowForm(false);

      await loadUsers();

    } catch (error) {
      console.error("Could not create user:", error);

      setError(
        error.response?.data?.error ||
        "Could not create user."
      );
    }
  };

  const toggleUserStatus = async (user) => {
    try {
      await api.put(
        `/api/users/admin/users/${user.user_id}/status`,
        {
          is_active: !user.is_active
        }
      );

      await loadUsers();

    } catch (error) {
      console.error("Could not update user:", error);

      setError(
        error.response?.data?.error ||
        "Could not update user."
      );
    }
  };

  return (
    <div>

      <div className="page-header">
        <div>
          <h1>User Management</h1>

          <p className="muted">
            Manage system users and their store access.
          </p>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? "Cancel" : "Add User"}
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {showForm && (
        <div className="dashboard-section">

          <div className="section-header">
            <div>
              <h2>Add User</h2>

              <p className="muted">
                Create an OWNER or STAFF account.
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit}>

            <div className="form-grid">

              <div className="form-group">
                <label>Full Name</label>

                <input
                  type="text"
                  name="full_name"
                  value={form.full_name}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Username</label>

                <input
                  type="text"
                  name="username"
                  value={form.username}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Email</label>

                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Password</label>

                <input
                  type="password"
                  name="password"
                  value={form.password}
                  onChange={handleChange}
                  minLength={8}
                  required
                />
              </div>

              <div className="form-group">
                <label>Role</label>

                <select
                  name="role"
                  value={form.role}
                  onChange={handleChange}
                >
                  <option value="STAFF">
                    STAFF
                  </option>

                  <option value="OWNER">
                    OWNER
                  </option>
                </select>
              </div>

              <div className="form-group">
                <label>Store</label>

                <select
                  name="store_id"
                  value={form.store_id}
                  onChange={handleChange}
                  required
                >
                  <option value="">
                    Select Store
                  </option>

                  {stores.map((store) => (
                    <option
                      key={store.store_id}
                      value={store.store_id}
                    >
                      {store.store_name}
                    </option>
                  ))}
                </select>
              </div>

            </div>

            <button
              type="submit"
              className="btn btn-primary"
            >
              Create User
            </button>

          </form>

        </div>
      )}

      <div className="dashboard-section">

        <div className="section-header">
          <div>
            <h2>System Users</h2>

            <p className="muted">
              All users registered in the system.
            </p>
          </div>
        </div>

        {loading ? (
          <p>Loading users...</p>
        ) : users.length === 0 ? (
          <p className="muted">
            No users found.
          </p>
        ) : (
          <div className="table-wrapper">

            <table>

              <thead>
                <tr>
                  <th>Name</th>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Store</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>

                {users.map((user) => (
                  <tr key={user.user_id}>

                    <td>
                      {user.full_name}
                    </td>

                    <td>
                      {user.username}
                    </td>

                    <td>
                      {user.email}
                    </td>

                    <td>
                      {user.role}
                    </td>

                    <td>
                      {user.store_name || "No Store"}
                    </td>

                    <td>
                      {user.is_active
                        ? "Active"
                        : "Inactive"}
                    </td>

                    <td>
                      {user.role !== "ADMIN" && (
                        <button
                          className="btn btn-secondary"
                          onClick={() =>
                            toggleUserStatus(user)
                          }
                        >
                          {user.is_active
                            ? "Deactivate"
                            : "Activate"}
                        </button>
                      )}
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