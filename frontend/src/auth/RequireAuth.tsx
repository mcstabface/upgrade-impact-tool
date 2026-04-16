import { Navigate, Outlet, useLocation } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import { useAuth } from "./AuthContext";

export default function RequireAuth() {
    const { isAuthenticated, isLoading } = useAuth();
    const location = useLocation();

    if (isLoading) {
        return <LoadingState message="Loading session..." />;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace state={{ from: location }} />;
    }

    return <Outlet />;
}