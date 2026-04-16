export type UserRole = "VIEWER" | "ANALYST" | "REVIEWER" | "ADMIN";

let currentRole: UserRole = "VIEWER";

export function getCurrentRole(): UserRole {
    return currentRole;
}

export function setCurrentRole(role: UserRole) {
    currentRole = role;
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