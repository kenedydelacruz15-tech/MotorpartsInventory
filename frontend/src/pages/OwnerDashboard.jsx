import { Link } from "react-router-dom";

export default function OwnerDashboard() {
  return (
    <div>
      <h2>Owner Dashboard</h2>
      <p className="muted">Manage your store's products, categories, inventory and sales.</p>
      <div className="dashboard-grid">
        <Link className="module-card" to="/inventory"><strong>Inventory</strong><span>View current store stock.</span></Link>
        <Link className="module-card" to="/categories"><strong>Categories</strong><span>Create and manage store categories.</span></Link>
        <Link className="module-card" to="/products"><strong>Products</strong><span>Create and manage motorcycle parts.</span></Link>
        <Link className="module-card" to="/pos"><strong>POS / Sales</strong><span>Record store sales.</span></Link>
      </div>
    </div>
  );
}
