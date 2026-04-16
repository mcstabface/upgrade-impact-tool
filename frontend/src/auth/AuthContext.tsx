import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
    type ReactNode,
} from "react";

import { setCurrentRole, type UserRole } from "./role";
import {
    getMe,
    login as loginRequest,
    logout as logoutRequest,
    type AuthUser,
    type LoginRequest,
} from "../services/auth";

type AuthContextValue = {
    user: AuthUser | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (payload: LoginRequest) => Promise<void>;
    logout: () => Promise<void>;
    refreshSession: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<AuthUser | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const refreshSession = useCallback(async () => {
        try {
            const nextUser = await getMe();
            setUser(nextUser);
            setCurrentRole(nextUser.role);
        } catch {
            setUser(null);
            setCurrentRole("VIEWER");
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        void refreshSession();
    }, [refreshSession]);

    const login = useCallback(async (payload: LoginRequest) => {
        const nextUser = await loginRequest(payload);
        setUser(nextUser);
        setCurrentRole(nextUser.role);
    }, []);

    const logout = useCallback(async () => {
        try {
            await logoutRequest();
        } finally {
            setUser(null);
            setCurrentRole("VIEWER");
        }
    }, []);

    const value = useMemo<AuthContextValue>(
        () => ({
            user,
            isLoading,
            isAuthenticated: user !== null,
            login,
            logout,
            refreshSession,
        }),
        [user, isLoading, login, logout, refreshSession],
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const context = useContext(AuthContext);

    if (!context) {
        throw new Error("useAuth must be used inside AuthProvider");
    }

    return context;
}

export function useCurrentRole(): UserRole {
    return useAuth().user?.role ?? "VIEWER";
}