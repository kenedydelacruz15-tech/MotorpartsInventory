import { Link } from "react-router-dom";

export default function AdminDashboard() {
  return (
    <div>
      <h2>Admin Dashboard</h2>
      <p className="muted">System administration. Store inventory operations are handled by Owners and Staff.</p>
      <div className="dashboard-grid">
        <div className="module-card"><strong>System Management</strong><span>Manage system-level settings and administration.</span></div>
        <div className="module-card"><strong>Stores</strong><span>System-level store administration.</span></div>
        <Link className="module-card" to="/admin/users"><strong>Users</strong><span>View system users.</span></Link>
      </div>
    </div>
  );
}
