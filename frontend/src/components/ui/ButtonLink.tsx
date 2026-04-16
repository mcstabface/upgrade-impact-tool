import { Link } from "react-router-dom";

type ButtonLinkProps = {
    to: string;
    children: React.ReactNode;
    variant?: "default" | "primary" | "subtle";
};

export default function ButtonLink({
    to,
    children,
    variant = "default",
}: ButtonLinkProps) {
    const className =
        variant === "primary"
            ? "ui-button ui-button--primary"
            : variant === "subtle"
              ? "ui-button ui-button--subtle"
              : "ui-button";

    return (
        <Link to={to} className={className}>
            {children}
        </Link>
    );
}