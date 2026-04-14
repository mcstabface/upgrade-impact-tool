import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import StatusHelp from "../components/StatusHelp";
import { formatUnixSeconds } from "../utils/time";
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

  const reviewNote =
    data.summary.unknown_count > 0
      ? "Overall status requires review because unresolved unknown findings remain."
      : data.summary.blocked_count > 0
        ? "Overall status requires review because blocked findings remain."
        : data.summary.review_required_count > 0
          ? "Overall status requires review because review-required findings remain."
          : null;

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Analysis Overview</h1>
      <p>
        <Link to="/dashboard">Back to Dashboard</Link>
      </p>
      <p>Analysis ID: {data.analysis_id}</p>
      <p>
        {data.customer_name} — {data.environment_name}
      </p>
      <p>Status: {data.overall_status}</p>
           <p>Status: {data.overall_status}</p>
      <StatusHelp status={data.overall_status} />
      <p>Started: {formatUnixSeconds(data.started_utc)}</p>
      <p>Completed: {formatUnixSeconds(data.completed_utc)}</p>
      <p>Duration (ms): {data.duration_ms ?? "N/A"}</p> <p>
        Applies: {data.summary.applies_count} | Review Required: {data.summary.review_required_count} | Unknown:{" "}
        {data.summary.unknown_count} | Blocked: {data.summary.blocked_count}
      </p>

      <p>Status: {data.overall_status}</p>
      <p>Started: {formatUnixSeconds(data.started_utc)}</p>
      <p>Completed: {formatUnixSeconds(data.completed_utc)}</p>
      <p>Duration (ms): {data.duration_ms ?? "N/A"}</p>

      {data.top_risks.length > 0 && (
        <>
          <h2>Top Risks</h2>
          <ul>
            {data.top_risks.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}

      {data.top_actions.length > 0 && (
        <>
          <h2>Top Actions</h2>
          <ul>
            {data.top_actions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}

      {reviewNote && <p>{reviewNote}</p>}

      {data.assumptions.length > 0 && (
        <>
          <h2>Assumptions</h2>
          <ul>
            {data.assumptions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}

      {data.missing_inputs.length > 0 && (
        <>
          <h2>Missing Inputs</h2>
          <ul>
            {data.missing_inputs.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}

      {data.derived_risks.length > 0 && (
        <>
          <h2>Derived Risks</h2>
          <ul>
            {data.derived_risks.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}

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