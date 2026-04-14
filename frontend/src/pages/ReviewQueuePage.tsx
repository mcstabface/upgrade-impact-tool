import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import StatusHelp from "../components/StatusHelp";
import StatusBanner from "../components/StatusBanner";
import { formatStatusLabel } from "../utils/status";
import { getReviewQueue, type ReviewQueueResponse } from "../services/reviewQueue";

export default function ReviewQueuePage() {
  const [data, setData] = useState<ReviewQueueResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getReviewQueue().then(setData).catch((err: Error) => setError(err.message));
  }, []);

  if (error) {
    return (
      <ErrorState
        title="Could not load review queue"
        message={error}
      />
    );
  }

  if (!data) {
    return <LoadingState message="Loading unresolved review items..." />;
  }

  if (data.items.length === 0) {
    return (
      <EmptyState
        title="Review queue is clear"
        message="There are no unresolved unknown, blocked, or review-required findings right now."
      />
    );
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "64rem" }}>
      <h1>Review Queue</h1>
      <p>
        <Link to="/dashboard">Back to Dashboard</Link>
      </p>

      <ul>
        {data.items.map((item) => (
          <li key={item.finding_id} style={{ marginBottom: "1.5rem" }}>
            <div>
              <Link to={`/findings/${item.finding_id}`}>{item.headline}</Link>
              {" — "}
              {formatStatusLabel(item.finding_status)}
              {" — "}
              {item.application_name}
              {" — "}
              {item.analysis_id}
              {item.reason_for_status ? ` — ${item.reason_for_status}` : ""}
            </div>

            <StatusHelp status={item.finding_status} />
            <StatusBanner status={item.finding_status} />
          </li>
        ))}
      </ul>
    </main>
  );
}