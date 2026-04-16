import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import ErrorState from "../components/ErrorState";
import { useAuth } from "../auth/AuthContext";

type RedirectState = {
    from?: {
        pathname?: string;
    };
};

export default function LoginPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const { login, isAuthenticated, isLoading } = useAuth();

    const [email, setEmail] = useState("pilot.admin@example.com");
    const [password, setPassword] = useState("ChangeMeNow!123");
    const [working, setWorking] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const redirectState = location.state as RedirectState | undefined;
    const redirectTo = redirectState?.from?.pathname ?? "/dashboard";

    useEffect(() => {
        if (!isLoading && isAuthenticated) {
            navigate(redirectTo, { replace: true });
        }
    }, [isAuthenticated, isLoading, navigate, redirectTo]);

    async function handleSubmit(event: React.FormEvent) {
        event.preventDefault();
        setWorking(true);
        setError(null);

        try {
            await login({
                email,
                password,
            });
            navigate(redirectTo, { replace: true });
        } catch (err) {
            setError((err as Error).message);
        } finally {
            setWorking(false);
        }
    }

    return (
        <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "32rem" }}>
            <h1>Sign In</h1>
            <p>Use a pilot account to access the Upgrade Impact Analysis Tool.</p>

            <form onSubmit={handleSubmit}>
                <div style={{ marginBottom: "1rem" }}>
                    <label>Email </label>
                    <input
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        autoComplete="username"
                    />
                </div>

                <div style={{ marginBottom: "1rem" }}>
                    <label>Password </label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete="current-password"
                    />
                </div>

                <button type="submit" disabled={working}>
                    {working ? "Signing In..." : "Sign In"}
                </button>
            </form>

            {error && (
                <div style={{ marginTop: "2rem" }}>
                    <ErrorState title="Sign-in failed" message={error} />
                </div>
            )}
        </main>
    );
}