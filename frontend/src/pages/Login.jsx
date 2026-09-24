import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { saveAuth } from "../services/auth";

const roles = [
  {
    key: "ADMIN",
    title: "Admin",
    description: "System management and administration",
  },
  {
    key: "OWNER",
    title: "Owner",
    description: "Manage your store and store operations",
  },
  {
    key: "STAFF",
    title: "Staff",
    description: "Inventory and daily sales operations",
  },
];

export default function Login() {
  const navigate = useNavigate();

  const [selectedRole, setSelectedRole] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();

    setError("");

    if (!selectedRole) {
      setError("Please select your login type.");
      return;
    }

    if (!username.trim()) {
      setError("Please enter your username.");
      return;
    }

    if (!password) {
      setError("Please enter your password.");
      return;
    }

    setLoading(true);

    try {
      const res = await api.post("/api/users/login", {
        username: username.trim(),
        password: password,
      });

      console.log("LOGIN RESPONSE:", res.data);

      // Get user information from backend
      const user = res.data?.user;

      if (!user) {
        setError("Login successful, but user information was not returned.");
        return;
      }

      // Check role
      const actualRole = String(user.role || "").toUpperCase();

      if (!actualRole) {
        setError("Your account does not have a role assigned.");
        return;
      }

      if (actualRole !== selectedRole.toUpperCase()) {
        setError(
          `This account is ${actualRole} and cannot use the ${selectedRole} login.`
        );
        return;
      }

      // Check access token
      const token = res.data?.access_token;

      if (!token) {
        setError("Login successful, but no access token was returned.");
        console.error("Backend response does not contain access_token:", res.data);
        return;
      }

      // Save authentication information
      const saved = saveAuth({
        access_token: token,
        user: {
          ...user,
          role: actualRole,
        },
      });

      console.log("AUTH SAVED:", saved);
      console.log("TOKEN:", localStorage.getItem("token"));
      console.log("USER:", localStorage.getItem("user"));

      if (!saved) {
        setError(
          "Login succeeded, but authentication information could not be saved."
        );
        return;
      }

      // Go to dashboard
      navigate("/dashboard", { replace: true });
    } catch (err) {
      console.error("LOGIN ERROR:", err);

      if (err.response) {
        console.error("SERVER RESPONSE:", err.response.data);

        setError(
          err.response.data?.error ||
            err.response.data?.message ||
            "Invalid username or password."
        );
      } else if (err.request) {
        setError(
          "Cannot connect to the backend. Make sure Flask is running on http://127.0.0.1:5000."
        );
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="role-login-page">
      <div className="role-login-card">

        <div className="login-heading">
          <h1>SmartInventory</h1>
          <p>Motorcycle Parts Inventory System</p>
        </div>

        <h3>Choose your account</h3>

        <div className="role-grid">
          {roles.map((role) => (
            <button
              type="button"
              key={role.key}
              className={`role-card ${
                selectedRole === role.key ? "selected" : ""
              }`}
              onClick={() => {
                setSelectedRole(role.key);
                setError("");
              }}
              disabled={loading}
            >
              <strong>{role.title}</strong>
              <span>{role.description}</span>
            </button>
          ))}
        </div>

        {selectedRole && (
          <form onSubmit={submit} className="login-form">

            <div className="selected-login">
              <span>Login as</span>
              <strong>{selectedRole}</strong>
            </div>

            {error && (
              <div className="alert">
                {error}
              </div>
            )}

            <label htmlFor="username">
              Username
            </label>

            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              disabled={loading}
              required
            />

            <label htmlFor="password">
              Password
            </label>

            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              disabled={loading}
              required
            />

            <button
              type="submit"
              className="primary full"
              disabled={loading}
            >
              {loading
                ? "Signing in..."
                : `Login as ${selectedRole}`}
            </button>

          </form>
        )}

      </div>
    </div>
  );
}