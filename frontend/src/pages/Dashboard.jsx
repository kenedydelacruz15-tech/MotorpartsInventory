import { Link } from "react-router-dom";

export default function Dashboard() {
  return (
    <div>
      <h2>Dashboard</h2>
      <p className="muted">Manage your store inventory and sales.</p>
      <div className="dashboard-grid">
        <Link className="module-card" to="/inventory"><strong>Inventory</strong><span>View current stock</span></Link>
        <Link className="module-card" to="/categories"><strong>Categories</strong><span>Manage product categories</span></Link>
        <Link className="module-card" to="/products"><strong>Products</strong><span>Manage motorcycle parts</span></Link>
        <Link className="module-card" to="/pos"><strong>POS / Sales</strong><span>Record a customer sale</span></Link>
      </div>
    </div>
  );
}
