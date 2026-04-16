import { useState } from "react";
import { Link } from "react-router-dom";

import type { NotificationItem } from "../services/notifications";

type Props = {
  unreadCount: number;
  items: NotificationItem[];
};

function severityLabel(severity: string) {
  if (severity === "HIGH") return "High";
  if (severity === "MEDIUM") return "Medium";
  if (severity === "LOW") return "Low";
  return severity;
}

export default function NotificationTray({ unreadCount, items }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  const previewHeadlines = items.slice(0, 3).map((item) => item.headline);
  const hiddenCount = Math.max(items.length - previewHeadlines.length, 0);

  return (
    <section
      style={{
        marginBottom: "2rem",
        border: "1px solid #ccc",
        padding: "1rem",
      }}
    >
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
          <h2 style={{ margin: 0 }}>Notifications</h2>
          <p style={{ margin: "0.5rem 0 0 0" }}>
            {unreadCount === 0
              ? "No active notifications."
              : `${unreadCount} active notification${unreadCount === 1 ? "" : "s"}.`}
          </p>
        </div>

        <button type="button" onClick={() => setIsOpen((current) => !current)}>
          {isOpen ? "Collapse Notifications" : `Open Notifications (${unreadCount})`}
        </button>
      </div>

      {!isOpen && items.length === 0 && (
        <div style={{ marginTop: "1rem" }}>
          <p style={{ marginBottom: 0 }}>
            When the system detects stale analyses or overdue review work, they will appear here.
          </p>
        </div>
      )}

      {!isOpen && items.length > 0 && (
        <div style={{ marginTop: "1rem" }}>
          <p style={{ marginBottom: "0.5rem" }}>
            Most recent notification{previewHeadlines.length === 1 ? "" : "s"}:
          </p>
          <ul style={{ marginTop: 0, marginBottom: 0 }}>
            {previewHeadlines.map((headline) => (
              <li key={headline}>{headline}</li>
            ))}
          </ul>
          {hiddenCount > 0 && (
            <p style={{ marginTop: "0.75rem", marginBottom: 0 }}>
              {hiddenCount} more notification{hiddenCount === 1 ? "" : "s"} hidden. Open the tray
              to view all.
            </p>
          )}
        </div>
      )}

      {isOpen && items.length > 0 && (
        <ul style={{ paddingLeft: 0, listStyle: "none", marginTop: "1rem", marginBottom: 0 }}>
          {items.map((item) => (
            <li
              key={item.notification_id}
              style={{
                border: "1px solid #ccc",
                padding: "1rem",
                marginBottom: "1rem",
              }}
            >
              <div style={{ marginBottom: "0.5rem" }}>
                <strong>{item.headline}</strong>
              </div>

              <div>{item.message}</div>

              <div style={{ marginTop: "0.5rem" }}>
                Severity: {severityLabel(item.severity)} | Type: {item.notification_type}
              </div>

              <div style={{ marginTop: "0.75rem" }}>
                <Link to={item.target_path}>Open Target</Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}