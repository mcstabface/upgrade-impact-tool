import { Link } from "react-router-dom";

import type { NotificationItem } from "../services/notifications";

type Props = {
  unreadCount: number;
  items: NotificationItem[];
};

export default function NotificationTray({ unreadCount, items }: Props) {
  return (
    <section style={{ marginBottom: "2rem" }}>
      <h2>Notifications</h2>
      <p>Unread notifications: {unreadCount}</p>

      {items.length === 0 ? (
        <p>No active notifications.</p>
      ) : (
        <ul style={{ paddingLeft: 0, listStyle: "none" }}>
          {items.map((item) => (
            <li
              key={item.notification_id}
              style={{
                border: "1px solid #ccc",
                padding: "1rem",
                marginBottom: "1rem",
              }}
            >
              <div>
                <strong>{item.headline}</strong>
              </div>
              <div>{item.message}</div>
              <div style={{ marginTop: "0.5rem" }}>
                Severity: {item.severity} | Type: {item.notification_type}
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