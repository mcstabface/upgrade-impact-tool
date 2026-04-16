import { useState } from "react";
import { Link } from "react-router-dom";

import Card from "./ui/Card";
import type { NotificationItem } from "../services/notifications";

type Props = {
    unreadCount: number;
    items: NotificationItem[];
    onMarkRead: (notificationId: string) => Promise<void>;
};

function severityLabel(severity: string) {
    if (severity === "HIGH") return "High";
    if (severity === "MEDIUM") return "Medium";
    if (severity === "LOW") return "Low";
    return severity;
}

export default function NotificationTray({ unreadCount, items, onMarkRead }: Props) {
    const [isOpen, setIsOpen] = useState(false);
    const [workingNotificationId, setWorkingNotificationId] = useState<string | null>(null);

    const previewHeadlines = items.slice(0, 3).map((item) => item.headline);
    const hiddenCount = Math.max(items.length - previewHeadlines.length, 0);

    async function handleMarkRead(notificationId: string) {
        setWorkingNotificationId(notificationId);
        try {
            await onMarkRead(notificationId);
        } finally {
            setWorkingNotificationId(null);
        }
    }

    return (
        <Card title="Notifications" muted>
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: "1rem",
                    flexWrap: "wrap",
                }}
            >
                <div>
                    <p style={{ margin: 0, color: "var(--text-secondary)" }}>
                        {items.length === 0
                            ? "No active notifications."
                            : `${items.length} active notification${items.length === 1 ? "" : "s"}; ${unreadCount} unread.`}
                    </p>
                </div>

                <button
                    type="button"
                    className="ui-button ui-button--subtle"
                    onClick={() => setIsOpen((current) => !current)}
                >
                    {isOpen ? "Collapse Notifications" : `Open Notifications (${unreadCount})`}
                </button>
            </div>

            {!isOpen && items.length === 0 ? (
                <p className="ui-status-note">
                    When the system detects stale analyses or overdue review work, they will appear here.
                </p>
            ) : null}

            {!isOpen && items.length > 0 ? (
                <div style={{ marginTop: "1rem" }}>
                    <p style={{ marginBottom: "0.5rem", color: "var(--text-secondary)" }}>
                        Most recent notification{previewHeadlines.length === 1 ? "" : "s"}:
                    </p>
                    <ul className="ui-list ui-list--compact">
                        {previewHeadlines.map((headline) => (
                            <li key={headline}>{headline}</li>
                        ))}
                    </ul>
                    {hiddenCount > 0 ? (
                        <p className="ui-status-note">
                            {hiddenCount} more notification{hiddenCount === 1 ? "" : "s"} hidden. Open the tray
                            to view all.
                        </p>
                    ) : null}
                </div>
            ) : null}

            {isOpen && items.length > 0 ? (
                <div style={{ marginTop: "1rem" }}>
                    {items.map((item) => (
                        <article
                            key={item.notification_id}
                            className={`ui-notification-item ${item.is_read ? "" : "ui-notification-item--unread"}`}
                            style={{ opacity: item.is_read ? 0.82 : 1 }}
                        >
                            <div style={{ marginBottom: "0.5rem" }}>
                                <strong>{item.headline}</strong>
                            </div>

                            <div>{item.message}</div>

                            <div className="ui-status-note">
                                Severity: {severityLabel(item.severity)} | Type: {item.notification_type} | Status:{" "}
                                {item.is_read ? "Read" : "Unread"}
                            </div>

                            <div className="ui-inline-actions" style={{ marginTop: "0.9rem" }}>
                                <Link to={item.target_path}>Open Target</Link>
                                {!item.is_read ? (
                                    <button
                                        type="button"
                                        className="ui-button"
                                        onClick={() => handleMarkRead(item.notification_id)}
                                        disabled={workingNotificationId === item.notification_id}
                                    >
                                        {workingNotificationId === item.notification_id ? "Marking..." : "Mark Read"}
                                    </button>
                                ) : null}
                            </div>
                        </article>
                    ))}
                </div>
            ) : null}
        </Card>
    );
}