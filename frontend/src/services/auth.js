export function saveAuth(data) {
  if (!data?.access_token || !data?.user) {
    return false;
  }

  localStorage.setItem("token", data.access_token);
  localStorage.setItem("user", JSON.stringify(data.user));
  localStorage.setItem("role", data.user.role);

  return true;
}

export function getToken() {
  return localStorage.getItem("token");
}

export function getUser() {
  const user = localStorage.getItem("user");

  if (!user) {
    return null;
  }

  try {
    return JSON.parse(user);
  } catch {
    localStorage.removeItem("user");
    return null;
  }
}

export function getRole() {
  return getUser()?.role || null;
}

export function isLoggedIn() {
  return Boolean(getToken() && getUser());
}

export function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  localStorage.removeItem("role");
}