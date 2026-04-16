import type { ReactNode } from "react";

type CardProps = {
    title?: string;
    children: ReactNode;
    muted?: boolean;
    tone?: "default" | "warning" | "danger";
};

export default function Card({
    title,
    children,
    muted = false,
    tone = "default",
}: CardProps) {
    const classNames = [
        "ui-card",
        muted ? "ui-card--muted" : "",
        tone === "warning" ? "ui-card--warning" : "",
        tone === "danger" ? "ui-card--danger" : "",
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <section className={classNames}>
            {title ? <h2 className="ui-card__title">{title}</h2> : null}
            <div className="ui-card__body">{children}</div>
        </section>
    );
}