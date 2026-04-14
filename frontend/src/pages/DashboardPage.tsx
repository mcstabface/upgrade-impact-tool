import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import { getDashboard, type DashboardResponse } from "../services/dashboard";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboard().then(setData).catch((err: Error) => setError(err.message));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;
  if (data.analyses.length === 0) return <EmptyState message="No analyses found." />;

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Dashboard</h1>
      <p>
        <Link to="/intakes/new">Create Intake</Link>
      </p>
      <h2>Top Risks</h2>
      <ul>
        {data.top_risks.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h2>Top Actions</h2>
      <ul>
        {data.top_actions.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      {data.analyses.map((analysis) => (
        <article key={analysis.analysis_id} style={{ marginBottom: "1rem" }}>
          <h2>
            <Link to={`/analyses/${analysis.analysis_id}`}>
              {analysis.customer_name} — {analysis.environment_name}
            </Link>
          </h2>
          <p>Status: {analysis.overall_status}</p>
          <p>
            Applies: {analysis.applies_count} | Review Required:{" "}
            {analysis.review_required_count} | Unknown: {analysis.unknown_count}
          </p>
          <p>
            <Link to="/review-queue">Open Review Queue</Link>
          </p>
        </article>
      ))}
    </main>
  );
}