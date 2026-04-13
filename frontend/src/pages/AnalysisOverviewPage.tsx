import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import { getAnalysisOverview, type AnalysisOverviewResponse } from "../services/analyses";

export default function AnalysisOverviewPage() {
  const { id } = useParams();
  const [data, setData] = useState<AnalysisOverviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getAnalysisOverview(id).then(setData).catch((err: Error) => setError(err.message));
  }, [id]);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Analysis Overview</h1>
      <p>{data.customer_name} — {data.environment_name}</p>
      <p>Status: {data.overall_status}</p>
      <p>
        Applies: {data.summary.applies_count} | Review Required: {data.summary.review_required_count}
      </p>

      <h2>Applications</h2>
      <ul>
        {data.applications.map((app) => (
          <li key={app.analysis_application_id}>
            <Link to={`/analyses/${data.analysis_id}/applications/${app.analysis_application_id}`}>
              {app.application_name}
            </Link>{" "}
            — {app.status}
          </li>
        ))}
      </ul>
    </main>
  );
}