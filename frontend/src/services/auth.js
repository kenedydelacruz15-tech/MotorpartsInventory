export function saveAuth(data) {
  if (!data?.access_token || !data?.user) {
    return false;
  }

  const user = {
    ...data.user,
    role: String(data.user.role || "").toUpperCase(),
  };

  localStorage.setItem("token", data.access_token);
  localStorage.setItem("user", JSON.stringify(user));
  localStorage.setItem("role", user.role);

  return true;
}

export function getToken() {
  return localStorage.getItem("token");
}

export function getUser() {
  const storedUser = localStorage.getItem("user");

  if (!storedUser) {
    return null;
  }

  try {
    const user = JSON.parse(storedUser);

    if (!user || typeof user !== "object") {
      return null;
    }

    return {
      ...user,
      role: String(user.role || "").toUpperCase(),
    };
  } catch (error) {
    console.error("Invalid stored user:", error);

    localStorage.removeItem("user");
    localStorage.removeItem("role");

    return null;
  }
}

export function getRole() {
  const user = getUser();

  if (user?.role) {
    return user.role.toUpperCase();
  }

  const storedRole = localStorage.getItem("role");

  return storedRole
    ? storedRole.toUpperCase()
    : null;
}

export function isLoggedIn() {
  return Boolean(getToken() && getUser());
}

export function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  localStorage.removeItem("role");
}

export function getAuth() {
  return {
    token: getToken(),
    user: getUser(),
    role: getRole(),
    authenticated: isLoggedIn(),
  };
}