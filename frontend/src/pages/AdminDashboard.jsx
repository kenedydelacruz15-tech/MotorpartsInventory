import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

export default function AdminDashboard() {
  const [users, setUsers] = useState([]);
  const [stores, setStores] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setError("");

      // Load users and stores at the same time.
      const [usersRes, storesRes] = await Promise.all([
        api.get("/api/users/admin/users"),
        api.get("/api/store")
      ]);

      setUsers(usersRes.data);
      setStores(storesRes.data);

    } catch (error) {
      console.error(
        "Could not load admin dashboard:",
        error
      );

      setError(
        error.response?.data?.error ||
        "Could not load admin dashboard data."
      );

    } finally {
      setLoading(false);
    }
  };

  const totalUsers = users.length;

  const activeUsers = users.filter(
    (user) => user.is_active
  ).length;

  const inactiveUsers = users.filter(
    (user) => !user.is_active
  ).length;

  const ownerCount = users.filter(
    (user) => user.role === "OWNER"
  ).length;

  const staffCount = users.filter(
    (user) => user.role === "STAFF"
  ).length;

  return (
    <div>

      {/* Page header */}
      <div className="page-header">
        <div>
          <h1>Admin Dashboard</h1>

          <p className="muted">
            Overview of system administration and user management.
          </p>
        </div>

        <button
          className="btn btn-secondary"
          onClick={loadDashboard}
        >
          Refresh
        </button>
      </div>


      {/* Error message */}
      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}


      {/* System statistics */}
      <div className="dashboard-stats">

        <div className="stat-card">
          <span className="stat-label">
            System
          </span>

          <strong>
            {loading ? "..." : "Active"}
          </strong>

          <small>
            System is running normally
          </small>
        </div>


        <div className="stat-card">
          <span className="stat-label">
            Stores
          </span>

          <strong>
            {loading ? "..." : stores.length}
          </strong>

          <small>
            Registered stores
          </small>
        </div>


        <div className="stat-card">
          <span className="stat-label">
            Total Users
          </span>

          <strong>
            {loading ? "..." : totalUsers}
          </strong>

          <small>
            System users
          </small>
        </div>


        <div className="stat-card">
          <span className="stat-label">
            Active Users
          </span>

          <strong>
            {loading ? "..." : activeUsers}
          </strong>

          <small>
            Active accounts
          </small>
        </div>

      </div>


      {/* User overview */}
      <div className="dashboard-section">

        <div className="section-header">
          <div>
            <h2>User Overview</h2>

            <p className="muted">
              Current system user accounts.
            </p>
          </div>
        </div>


        <div className="dashboard-stats">

          <div className="stat-card">
            <span className="stat-label">
              Owners
            </span>

            <strong>
              {loading ? "..." : ownerCount}
            </strong>

            <small>
              Store owners
            </small>
          </div>


          <div className="stat-card">
            <span className="stat-label">
              Staff
            </span>

            <strong>
              {loading ? "..." : staffCount}
            </strong>

            <small>
              Store staff
            </small>
          </div>


          <div className="stat-card">
            <span className="stat-label">
              Inactive
            </span>

            <strong>
              {loading ? "..." : inactiveUsers}
            </strong>

            <small>
              Deactivated accounts
            </small>
          </div>

        </div>

      </div>


      {/* System management */}
      <div className="dashboard-section">

        <div className="section-header">
          <div>
            <h2>System Overview</h2>

            <p className="muted">
              Administrative functions available to you.
            </p>
          </div>
        </div>


        <div className="dashboard-grid">

          <div className="module-card">
            <strong>
              System Management
            </strong>

            <span>
              Manage system-level settings and administration.
            </span>
          </div>


          <Link className="module-card" to="/admin/stores">
            <strong>Stores</strong>
            <span>
              {stores.length} registered store
              {stores.length !== 1 ? "s" : ""}.
            </span>
          </Link>


          <Link
            className="module-card"
            to="/admin/users"
          >
            <strong>
              Users
            </strong>

            <span>
              View and manage system users.
            </span>
          </Link>

        </div>

      </div>


      {/* Admin access information */}
      <div className="dashboard-section">

        <div className="info-panel">

          <strong>
            Administrator Access
          </strong>

          <p className="muted">
            Admin accounts are responsible for
            system-level management. Store inventory
            and sales operations are handled by Owners
            and Staff.
          </p>

        </div>

      </div>

    </div>
  );
}