import {
  BrowserRouter,
  NavLink,
  Navigate,
  Route,
  Routes,
  useNavigate,
} from "react-router-dom";

import Login from "./pages/Login";
import AdminDashboard from "./pages/AdminDashboard";
import OwnerDashboard from "./pages/OwnerDashboard";
import StaffDashboard from "./pages/StaffDashboard";
import Categories from "./pages/Categories";
import Products from "./pages/Products";
import Inventory from "./pages/Inventory";
import POS from "./pages/POS";
import StoreSettings from "./pages/StoreSettings";
import AdminUsers from "./pages/AdminUsers";
import AdminStores from "./pages/AdminStores";
import StaffManagement from "./pages/StaffManagement";

import {
  getRole,
  getUser,
  isLoggedIn,
  logout,
} from "./services/auth";

import "./styles.css";


function Protected({ children, roles }) {
  if (!isLoggedIn()) {
    return <Navigate to="/login" replace />;
  }

  const role = getRole();

  if (roles && !roles.includes(role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}


function Layout() {
  const navigate = useNavigate();

  const user = getUser();
  const userRole = getRole();

  const signOut = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="app">

      <aside>

        <h2>SmartInventory</h2>

        <div className="user-box">

          <strong>
            {user?.full_name || user?.username || "User"}
          </strong>

          <small>
            {userRole}
          </small>

          {user?.store_id && (
            <small>
              Store ID: {user.store_id}
            </small>
          )}

        </div>


        <nav>

          <NavLink to="/dashboard">
            Dashboard
          </NavLink>


          {userRole === "ADMIN" && (
            <>
              <NavLink to="/admin/stores">
                Stores
              </NavLink>

              <NavLink to="/admin/users">
                Users
              </NavLink>
            </>
          )}


          {(userRole === "OWNER" || userRole === "STAFF") && (
            <>
              <NavLink to="/inventory">
                Inventory
              </NavLink>

              <NavLink to="/pos">
                POS / Sales
              </NavLink>
            </>
          )}


          {userRole === "OWNER" && (
            <>
              <NavLink to="/categories">
                Categories
              </NavLink>

              <NavLink to="/products">
                Products
              </NavLink>

              <NavLink to="/staff">
                Staff
              </NavLink>

              <NavLink to="/settings/store">
                Store Settings
              </NavLink>
            </>
          )}

        </nav>


        <button
          className="logout"
          onClick={signOut}
        >
          Logout
        </button>

      </aside>


      <main>

        <Routes>

          {/* Dashboard */}

          <Route
            path="/dashboard"
            element={
              <Protected>
                {userRole === "ADMIN" ? (
                  <AdminDashboard />
                ) : userRole === "OWNER" ? (
                  <OwnerDashboard />
                ) : (
                  <StaffDashboard />
                )}
              </Protected>
            }
          />


          {/* Inventory */}

          <Route
            path="/inventory"
            element={
              <Protected roles={["OWNER", "STAFF"]}>
                <Inventory />
              </Protected>
            }
          />


          {/* POS */}

          <Route
            path="/pos"
            element={
              <Protected roles={["OWNER", "STAFF"]}>
                <POS />
              </Protected>
            }
          />


          {/* Categories */}

          <Route
            path="/categories"
            element={
              <Protected roles={["OWNER"]}>
                <Categories />
              </Protected>
            }
          />


          {/* Products */}

          <Route
            path="/products"
            element={
              <Protected roles={["OWNER"]}>
                <Products />
              </Protected>
            }
          />

          {/* Staff Management */}

          <Route
            path="/staff"
            element={
              <Protected roles={["OWNER"]}>
                <StaffManagement />
              </Protected>
            }
          />


          {/* Store Settings */}

          <Route
            path="/settings/store"
            element={
              <Protected roles={["OWNER"]}>
                <StoreSettings />
              </Protected>
            }
          />


          {/* Admin Users */}
         <Route
            path="/admin/stores"
            element={
              <Protected roles={["ADMIN"]}>
                <AdminStores />
              </Protected>
            }
          />

          <Route
            path="/admin/users"
            element={
              <Protected roles={["ADMIN"]}>
                <AdminUsers />
              </Protected>
            }
          />


          {/* Default */}

          <Route
            path="/"
            element={
              <Navigate
                to="/dashboard"
                replace
              />
            }
          />


          <Route
            path="*"
            element={
              <Navigate
                to="/dashboard"
                replace
              />
            }
          />

        </Routes>

      </main>

    </div>
  );
}


export default function App() {

  return (
    <BrowserRouter>

      <Routes>

        {/* Login */}

        <Route
          path="/login"
          element={<Login />}
        />


        {/* Protected application */}

        <Route
          path="/*"
          element={
            <Protected>
              <Layout />
            </Protected>
          }
        />

      </Routes>

    </BrowserRouter>
  );
}