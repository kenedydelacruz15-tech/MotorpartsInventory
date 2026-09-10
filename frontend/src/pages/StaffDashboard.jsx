import { Link } from "react-router-dom";

export default function StaffDashboard() {
  return (
    <div>
      <h2>Staff Dashboard</h2>
      <p className="muted">Daily store operations.</p>
      <div className="dashboard-grid">
        <Link className="module-card" to="/inventory"><strong>Inventory</strong><span>View current stock.</span></Link>
        <Link className="module-card" to="/pos"><strong>POS / Sales</strong><span>Record customer sales.</span></Link>
      </div>
    </div>
  );
}
