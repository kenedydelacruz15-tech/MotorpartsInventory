import { useEffect, useState } from "react";
import api from "../services/api";

export default function Categories() {
  const [items, setItems] = useState([]);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const [editingId, setEditingId] = useState(null);

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("active");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const loadCategories = async () => {
    try {
      setLoading(true);
      setError("");

      const res = await api.get("/api/categories/", {
        params: {
          status,
          search,
        },
      });

      setItems(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      setError(
        err.response?.data?.message ||
        err.response?.data?.error ||
        "Could not load categories."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCategories();
  }, [status]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setSuccess("");

    if (!name.trim()) {
      setError("Category name is required.");
      return;
    }

    try {
      if (editingId) {
        await api.put(`/api/categories/${editingId}`, {
          category_name: name,
          description,
        });

        setSuccess("Category updated successfully.");
      } else {
        await api.post("/api/categories/", {
          category_name: name,
          description,
        });

        setSuccess("Category created successfully.");
      }

      resetForm();
      loadCategories();
    } catch (err) {
      setError(
        err.response?.data?.message ||
        err.response?.data?.error ||
        "Something went wrong."
      );
    }
  };

  const handleEdit = (category) => {
    setEditingId(category.category_id);
    setName(category.category_name);
    setDescription(category.description || "");

    setError("");
    setSuccess("");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const handleDeactivate = async (category) => {
    const confirmed = window.confirm(
      `Deactivate "${category.category_name}"?`
    );

    if (!confirmed) {
      return;
    }

    setError("");
    setSuccess("");

    try {
      await api.put(
        `/api/categories/${category.category_id}/deactivate`
      );

      setSuccess("Category deactivated successfully.");

      loadCategories();
    } catch (err) {
      setError(
        err.response?.data?.message ||
        err.response?.data?.error ||
        "Could not deactivate category."
      );
    }
  };

  const handleRestore = async (category) => {
    const confirmed = window.confirm(
      `Restore "${category.category_name}"?`
    );

    if (!confirmed) {
      return;
    }

    setError("");
    setSuccess("");

    try {
      await api.put(
        `/api/categories/${category.category_id}/restore`
      );

      setSuccess("Category restored successfully.");

      loadCategories();
    } catch (err) {
      setError(
        err.response?.data?.message ||
        err.response?.data?.error ||
        "Could not restore category."
      );
    }
  };

  const resetForm = () => {
    setEditingId(null);
    setName("");
    setDescription("");
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadCategories();
  };

  return (
    <div className="categories-page">

      <div className="categories-header">
        <div>
          <h1>Categories</h1>
          <p>Manage product categories for your store.</p>
        </div>
      </div>

      {error && (
        <div className="alert">
          {error}
        </div>
      )}

      {success && (
        <div className="success">
          {success}
        </div>
      )}

      <div className="category-form-card">

        <div className="form-header">
          <div>
            <h2>
              {editingId
                ? "Edit Category"
                : "Add Category"}
            </h2>

            <p>
              {editingId
                ? "Update the selected category."
                : "Create a new product category."}
            </p>
          </div>
        </div>

        <form
          className="category-form"
          onSubmit={handleSubmit}
        >

          <div className="form-group">
            <label htmlFor="category-name">
              Category Name
            </label>

            <input
              id="category-name"
              type="text"
              placeholder="e.g. Brake System"
              value={name}
              onChange={(e) =>
                setName(e.target.value)
              }
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="category-description">
              Description
            </label>

            <input
              id="category-description"
              type="text"
              placeholder="Category description"
              value={description}
              onChange={(e) =>
                setDescription(e.target.value)
              }
            />
          </div>

          <div className="form-actions">

            <button
              type="submit"
              className="btn btn-primary"
            >
              {editingId
                ? "Update Category"
                : "Add Category"}
            </button>

            {editingId && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={resetForm}
              >
                Cancel
              </button>
            )}

          </div>

        </form>
      </div>

      <div className="categories-card">

        <div className="table-header">
          <h2>Category List</h2>

          <span>
            Manage active and inactive categories.
          </span>
        </div>

        <div className="categories-toolbar">

          <form
            className="search-box"
            onSubmit={handleSearch}
          >
            <input
              type="text"
              placeholder="Search categories..."
              value={search}
              onChange={(e) =>
                setSearch(e.target.value)
              }
            />

            <button
              type="submit"
              className="search-button"
            >
              Search
            </button>
          </form>

          <div className="status-filters">

            <button
              type="button"
              className={
                status === "active"
                  ? "filter-btn active"
                  : "filter-btn"
              }
              onClick={() => setStatus("active")}
            >
              Active
            </button>

            <button
              type="button"
              className={
                status === "inactive"
                  ? "filter-btn active"
                  : "filter-btn"
              }
              onClick={() => setStatus("inactive")}
            >
              Inactive
            </button>

            <button
              type="button"
              className={
                status === "all"
                  ? "filter-btn active"
                  : "filter-btn"
              }
              onClick={() => setStatus("all")}
            >
              All
            </button>

          </div>

        </div>

        <div className="table-container">

          <table>

            <thead>
              <tr>
                <th>ID</th>
                <th>Category</th>
                <th>Description</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>

              {loading ? (
                <tr>
                  <td
                    colSpan="5"
                    className="empty-state"
                  >
                    Loading categories...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td
                    colSpan="5"
                    className="empty-state"
                  >
                    <h3>No categories found</h3>
                    <p>
                      There are no categories matching
                      your current filter.
                    </p>
                  </td>
                </tr>
              ) : (
                items.map((category) => (
                  <tr
                    key={category.category_id}
                  >

                    <td>
                      {category.category_id}
                    </td>

                    <td>
                      <strong>
                        {category.category_name}
                      </strong>
                    </td>

                    <td>
                      {category.description || "-"}
                    </td>

                    <td>
                      {category.is_active ? (
                        <span className="status-badge active">
                          Active
                        </span>
                      ) : (
                        <span className="status-badge inactive">
                          Inactive
                        </span>
                      )}
                    </td>

                    <td>

                      <div className="action-buttons">

                        {category.is_active ? (
                          <>
                            <button
                              type="button"
                              className="action-button edit-button"
                              onClick={() =>
                                handleEdit(category)
                              }
                            >
                              <span className="action-icon">
                                ✎
                              </span>
                              Edit
                            </button>

                            <button
                              type="button"
                              className="action-button deactivate-button"
                              onClick={() =>
                                handleDeactivate(category)
                              }
                            >
                              <span className="action-icon">
                                ×
                              </span>
                              Delete
                            </button>
                          </>
                        ) : (
                          <button
                            type="button"
                            className="action-button restore-button"
                            onClick={() =>
                              handleRestore(category)
                            }
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
                ))
              )}

            </tbody>

          </table>

        </div>

      </div>

    </div>
  );
}