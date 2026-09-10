import { useEffect, useState } from "react";
import api from "../services/api";

const emptyForm = {
  product_name: "",
  sku: "",
  part_number: "",
  brand: "",
  category_id: "",
  selling_price: "",
  reorder_level: "10",
  description: "",
};

export default function Products() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);

  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);

  const [filter, setFilter] = useState("active");
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(false);
  const [loadingProducts, setLoadingProducts] = useState(true);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    loadProducts();
    loadCategories();
  }, [filter]);

  const loadProducts = async () => {
    try {
      setLoadingProducts(true);
      setError("");

      const params = {
        status: filter,
      };

      if (search.trim()) {
        params.search = search.trim();
      }

      const res = await api.get("/api/products/", {
        params,
      });

      const data = res.data;

      if (Array.isArray(data)) {
        setProducts(data);
      } else if (Array.isArray(data.products)) {
        setProducts(data.products);
      } else {
        setProducts([]);
      }
    } catch (err) {
      console.error("Load products error:", err);

      setError(
        err.response?.data?.error ||
          "Failed to load products."
      );

      setProducts([]);
    } finally {
      setLoadingProducts(false);
    }
  };

  const loadCategories = async () => {
    try {
      const res = await api.get("/api/categories/");

      const data = res.data;

      if (Array.isArray(data)) {
        setCategories(data);
      } else if (Array.isArray(data.categories)) {
        setCategories(data.categories);
      } else {
        setCategories([]);
      }
    } catch (err) {
      console.error("Load categories error:", err);

      setError(
        err.response?.data?.error ||
          "Failed to load categories."
      );
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));

    setError("");
    setSuccess("");
  };

  const resetForm = () => {
    setForm({ ...emptyForm });
    setEditingId(null);
    setError("");
    setSuccess("");
  };

  const handleSearch = async () => {
    await loadProducts();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setSuccess("");

    if (!form.product_name.trim()) {
      setError("Product name is required.");
      return;
    }

    if (!form.sku.trim()) {
      setError("SKU is required.");
      return;
    }

    if (!form.category_id) {
      setError("Please select a category.");
      return;
    }

    if (
      form.selling_price === "" ||
      Number(form.selling_price) < 0
    ) {
      setError("Please enter a valid selling price.");
      return;
    }

    if (
      form.reorder_level === "" ||
      Number(form.reorder_level) < 0
    ) {
      setError("Please enter a valid reorder level.");
      return;
    }

    const productData = {
      product_name: form.product_name.trim(),
      sku: form.sku.trim(),
      part_number: form.part_number.trim() || null,
      brand: form.brand.trim() || null,
      category_id: Number(form.category_id),
      selling_price: Number(form.selling_price),
      reorder_level: Number(form.reorder_level),
      description: form.description.trim() || null,
    };

    try {
      setLoading(true);

      if (editingId !== null) {
        await api.put(
          `/api/products/${editingId}`,
          productData
        );

        setSuccess("Product updated successfully.");
      } else {
        await api.post(
          "/api/products/",
          productData
        );

        setSuccess("Product added successfully.");
      }

      setForm({ ...emptyForm });
      setEditingId(null);

      await loadProducts();
    } catch (err) {
      console.error("Save product error:", err);

      setError(
        err.response?.data?.error ||
          err.response?.data?.message ||
          "Failed to save product."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (product) => {
    setEditingId(product.product_id);

    setForm({
      product_name: product.product_name || "",
      sku: product.sku || "",
      part_number: product.part_number || "",
      brand: product.brand || "",
      category_id: product.category_id
        ? String(product.category_id)
        : "",
      selling_price:
        product.selling_price !== null &&
        product.selling_price !== undefined
          ? String(product.selling_price)
          : "",
      reorder_level:
        product.reorder_level !== null &&
        product.reorder_level !== undefined
          ? String(product.reorder_level)
          : "10",
      description: product.description || "",
    });

    setError("");
    setSuccess("");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const handleDeactivate = async (product) => {
    const confirmed = window.confirm(
      `Deactivate "${product.product_name}"?\n\n` +
        "The product will be hidden from the active product list, " +
        "but its records and history will be preserved."
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");
      setSuccess("");

      await api.put(
        `/api/products/${product.product_id}/deactivate`
      );

      setSuccess(
        `"${product.product_name}" was deactivated successfully.`
      );

      if (editingId === product.product_id) {
        resetForm();
      }

      await loadProducts();
    } catch (err) {
      console.error(
        "Deactivate product error:",
        err
      );

      setError(
        err.response?.data?.error ||
          err.response?.data?.message ||
          "Failed to deactivate product."
      );
    }
  };

  const handleRestore = async (product) => {
    const confirmed = window.confirm(
      `Restore "${product.product_name}"?\n\n` +
        "The product will become active again."
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");
      setSuccess("");

      await api.put(
        `/api/products/${product.product_id}/restore`
      );

      setSuccess(
        `"${product.product_name}" was restored successfully.`
      );

      await loadProducts();
    } catch (err) {
      console.error(
        "Restore product error:",
        err
      );

      setError(
        err.response?.data?.error ||
          err.response?.data?.message ||
          "Failed to restore product."
      );
    }
  };

  const getCategoryName = (categoryId) => {
    const category = categories.find(
      (item) =>
        Number(item.category_id) ===
        Number(categoryId)
    );

    return category
      ? category.category_name
      : "Unknown";
  };

  return (
    <div className="page">

      <div className="page-header">
        <div>
          <h1>Products</h1>
          <p>
            Manage motorcycle parts and product information.
          </p>
        </div>
      </div>

      {error && (
        <div className="alert">
          {error}
        </div>
      )}

      {success && (
        <div className="alert success">
          {success}
        </div>
      )}

      <div className="product-form-card">

        <div className="form-header">
          <div>
            <h2>
              {editingId !== null
                ? "Edit Product"
                : "Add Product"}
            </h2>

            {editingId !== null && (
              <p>
                You are currently editing product ID #
                {editingId}
              </p>
            )}
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="product-form"
        >

          <div className="form-field">
            <label>Product Name</label>

            <input
              type="text"
              name="product_name"
              placeholder="Enter product name"
              value={form.product_name}
              onChange={handleChange}
              disabled={loading}
              required
            />
          </div>

          <div className="form-field">
            <label>SKU</label>

            <input
              type="text"
              name="sku"
              placeholder="Example: BP-001"
              value={form.sku}
              onChange={handleChange}
              disabled={loading}
              required
            />
          </div>

          <div className="form-field">
            <label>Part Number / Barcode</label>

            <input
              type="text"
              name="part_number"
              placeholder="Part number or barcode"
              value={form.part_number}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="form-field">
            <label>Brand</label>

            <input
              type="text"
              name="brand"
              placeholder="Example: Honda"
              value={form.brand}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="form-field">
            <label>Category</label>

            <select
              name="category_id"
              value={form.category_id}
              onChange={handleChange}
              disabled={loading}
              required
            >
              <option value="">
                Select Category
              </option>

              {categories.map((category) => (
                <option
                  key={category.category_id}
                  value={category.category_id}
                >
                  {category.category_name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-field">
            <label>Selling Price</label>

            <input
              type="number"
              name="selling_price"
              placeholder="0.00"
              value={form.selling_price}
              onChange={handleChange}
              min="0"
              step="0.01"
              disabled={loading}
              required
            />
          </div>

          <div className="form-field">
            <label>Reorder Level</label>

            <input
              type="number"
              name="reorder_level"
              placeholder="10"
              value={form.reorder_level}
              onChange={handleChange}
              min="0"
              step="1"
              disabled={loading}
              required
            />
          </div>

          <div className="form-field full-width">
            <label>Description</label>

            <input
              type="text"
              name="description"
              placeholder="Product description"
              value={form.description}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="product-form-buttons">

            <button
              type="submit"
              className="primary update-button"
              disabled={loading}
            >
              {loading
                ? "Saving..."
                : editingId !== null
                ? "✓ Update Product"
                : "+ Add Product"}
            </button>

            {editingId !== null && (
              <button
                type="button"
                className="secondary cancel-button"
                onClick={resetForm}
                disabled={loading}
              >
                ✕ Cancel
              </button>
            )}

          </div>

        </form>

      </div>

      <div className="product-toolbar">

        <div className="search-box">

          <input
            type="text"
            placeholder="Search product, SKU, brand..."
            value={search}
            onChange={(e) =>
              setSearch(e.target.value)
            }
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSearch();
              }
            }}
          />

          <button
            type="button"
            className="search-button"
            onClick={handleSearch}
          >
            Search
          </button>

        </div>

        <div className="filter-box">

          <label>Status</label>

          <select
            value={filter}
            onChange={(e) =>
              setFilter(e.target.value)
            }
          >
            <option value="active">
              Active Products
            </option>

            <option value="inactive">
              Inactive Products
            </option>

            <option value="all">
              All Products
            </option>
          </select>

        </div>

      </div>

      <div className="table-container">

        {loadingProducts ? (
          <div className="empty-state">
            <p>Loading products...</p>
          </div>
        ) : products.length === 0 ? (
          <div className="empty-state">
            <h3>No products found</h3>

            <p>
              {filter === "active"
                ? "There are no active products."
                : filter === "inactive"
                ? "There are no inactive products."
                : "No products are available."}
            </p>
          </div>
        ) : (
          <table>

            <thead>
              <tr>
                <th>ID</th>
                <th>Product</th>
                <th>SKU</th>
                <th>Part Number</th>
                <th>Brand</th>
                <th>Category</th>
                <th>Price</th>
                <th>Reorder</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>

              {products.map((product) => {

                const isActive =
                  Number(product.is_active) === 1;

                return (
                  <tr
                    key={product.product_id}
                  >

                    <td>
                      {product.product_id}
                    </td>

                    <td>
                      <strong>
                        {product.product_name}
                      </strong>
                    </td>

                    <td>
                      {product.sku}
                    </td>

                    <td>
                      {product.part_number || "-"}
                    </td>

                    <td>
                      {product.brand || "-"}
                    </td>

                    <td>
                      {product.category_name ||
                        getCategoryName(
                          product.category_id
                        )}
                    </td>

                    <td>
                      ₱
                      {Number(
                        product.selling_price || 0
                      ).toFixed(2)}
                    </td>

                    <td>
                      {product.reorder_level}
                    </td>

                    <td>

                      <span
                        className={
                          isActive
                            ? "status-badge active-status"
                            : "status-badge inactive-status"
                        }
                      >
                        {isActive
                          ? "Active"
                          : "Inactive"}
                      </span>

                    </td>

                    <td>

                      <div className="action-buttons">

                        <button
                          type="button"
                          className="action-button edit-button"
                          onClick={() =>
                            handleEdit(product)
                          }
                          disabled={loading}
                          title="Edit product"
                        >
                          <span className="action-icon">
                            ✎
                          </span>

                          Edit
                        </button>

                        {isActive ? (
                          <button
                            type="button"
                            className="action-button deactivate-button"
                            onClick={() =>
                              handleDeactivate(
                                product
                              )
                            }
                            disabled={loading}
                            title="Deactivate product"
                          >
                            <span className="action-icon">
                              ⏸
                            </span>

                            Deactivate
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="action-button restore-button"
                            onClick={() =>
                              handleRestore(
                                product
                              )
                            }
                            disabled={loading}
                            title="Restore product"
                          >
                            <span className="action-icon">
                              ↻
                            </span>

                            Restore
                          </button>
                        )}

                      </div>

                    </td>

                  </tr>
                );
              })}

            </tbody>

          </table>
        )}

      </div>

    </div>
  );
}