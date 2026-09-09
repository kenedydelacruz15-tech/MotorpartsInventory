import { useState } from 'react';
import axios from 'axios';

function App() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState('');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const login = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/users/login', {
        username,
        password,
      });

      const accessToken = response.data.access_token;
      setToken(accessToken);
      await fetchProducts(accessToken);
    } catch (err) {
      setError(err?.response?.data?.error || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async (authToken) => {
    try {
      const response = await axios.get('/api/products/', {
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`,
        },
      });

      setProducts(response.data);
    } catch (err) {
      const apiError = err?.response?.data?.error || 'Unable to load products.';
      setError(apiError);
    }
  };

  return (
    <div className="container py-4">
      <div className="row">
        <div className="col-md-12">
          <div className="card shadow">
            <div className="card-header bg-dark text-white">
              <div className="d-flex justify-content-between align-items-center">
                <h4 className="mb-0">Motor Parts Inventory</h4>
                {token && (
                  <button className="btn btn-outline-light btn-sm" onClick={() => setToken('')}>
                    Logout
                  </button>
                )}
              </div>
            </div>

            <div className="card-body">
              {!token ? (
                <form onSubmit={login} className="row g-3 align-items-end">
                  <div className="col-md-4">
                    <label className="form-label">Username</label>
                    <input
                      type="text"
                      className="form-control"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      required
                    />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label">Password</label>
                    <input
                      type="password"
                      className="form-control"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                  </div>
                  <div className="col-md-4">
                    <button className="btn btn-primary w-100" type="submit" disabled={loading}>
                      {loading ? 'Loading...' : 'Login'}
                    </button>
                  </div>

                  {error && (
                    <div className="col-md-12">
                      <div className="alert alert-danger mb-0">{error}</div>
                    </div>
                  )}
                </form>
              ) : (
                <div className="d-flex justify-content-between align-items-center">
                  <span className="fw-bold">Connected to Motor Parts API</span>
                </div>
              )}
            </div>
          </div>

          {token && (
            <div className="card mt-4 shadow">
              <div className="card-body">
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <h5 className="mb-0">Product Catalog</h5>
                  <span className="badge text-bg-success">API Connected</span>
                </div>

                <div className="table-responsive">
                  <table className="table table-striped table-bordered align-middle">
                    <thead className="table-dark">
                      <tr>
                        <th>#</th>
                        <th>Product Name</th>
                        <th>SKU</th>
                        <th>Part Number</th>
                        <th>Brand</th>
                        <th>Category</th>
                        <th>Selling Price</th>
                        <th>Reorder Level</th>
                      </tr>
                    </thead>
                    <tbody>
                      {products.length > 0 ? (
                        products.map((product, index) => (
                          <tr key={product.product_id}>
                            <td>{index + 1}</td>
                            <td>{product.product_name}</td>
                            <td>{product.sku}</td>
                            <td>{product.part_number || '—'}</td>
                            <td>{product.brand || '—'}</td>
                            <td>{product.category_name}</td>
                            <td>{product.selling_price}</td>
                            <td>{product.reorder_level}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="8" className="text-center">
                            No products found.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
