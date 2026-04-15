export type UserRole = "VIEWER" | "ANALYST" | "REVIEWER" | "ADMIN";

const ROLE_STORAGE_KEY = "upgrade-impact-tool-role";

export function getCurrentRole(): UserRole {
  if (typeof window === "undefined") {
    return "VIEWER";
  }

  const storedValue = window.localStorage.getItem(ROLE_STORAGE_KEY);
  if (
    storedValue === "VIEWER" ||
    storedValue === "ANALYST" ||
    storedValue === "REVIEWER" ||
    storedValue === "ADMIN"
  ) {
    return storedValue;
  }

  return "VIEWER";
}

export function setCurrentRole(role: UserRole) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(ROLE_STORAGE_KEY, role);
}

export function isAdminRole(role: UserRole) {
  return role === "ADMIN";
}

export function canManageIntakes(role: UserRole) {
  return role === "ANALYST" || role === "ADMIN";
}

export function canManageReviews(role: UserRole) {
  return role === "REVIEWER" || role === "ADMIN";
}