import type { ReactNode } from "react";

type AppShellProps = {
    title: string;
    subtitle?: string;
    actions?: ReactNode;
    children: ReactNode;
};

export default function AppShell({
    title,
    subtitle,
    actions,
    children,
}: AppShellProps) {
    return (
        <main className="ui-shell">
            <header className="ui-page-header">
                <div>
                    <h1 className="ui-page-title">{title}</h1>
                    {subtitle ? <p className="ui-page-subtitle">{subtitle}</p> : null}
                </div>
                {actions ? <div className="ui-inline-actions">{actions}</div> : null}
            </header>

            {children}
        </main>
    );
}