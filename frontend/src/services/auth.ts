import { apiGet, apiPost, apiPostNoContent } from "./api";
import type { UserRole } from "../auth/role";

export type AuthUser = {
    user_id: string;
    email: string;
    display_name: string;
    role: UserRole;
};

export type LoginRequest = {
    email: string;
    password: string;
};

export function getMe() {
    return apiGet<AuthUser>("/auth/me");
}

export function login(payload: LoginRequest) {
    return apiPost<AuthUser, LoginRequest>("/auth/login", payload);
}

export function logout() {
    return apiPostNoContent("/auth/logout", {});
}