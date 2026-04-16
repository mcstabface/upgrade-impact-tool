import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import type { UserRole } from "./role";
import { useAuth } from "./AuthContext";

export default function RequireRole({
    allowedRoles,
    children,
}: {
    allowedRoles: UserRole[];
    children: ReactNode;
}) {
    const { user } = useAuth();

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    if (!allowedRoles.includes(user.role)) {
        return <Navigate to="/dashboard" replace />;
    }

    return <>{children}</>;
}