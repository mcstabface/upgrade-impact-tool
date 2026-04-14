import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import StatusHelp from "../components/StatusHelp";
import { formatUnixSeconds } from "../utils/time";
import { getDashboard, type DashboardResponse } from "../services/dashboard";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboard().then(setData).catch((err: Error) => setError(err.message));
  }, []);

  const latestCompletedAnalysis = useMemo(() => {
    if (!data) return null;

    return (
      data.analyses.find((analysis) => analysis.analysis_date !== null) ?? null
    );
  }, [data]);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;
  if (data.analyses.length === 0) return <EmptyState message="No analyses found." />;

  const topRisks = data.top_risks ?? [];
  const topActions = data.top_actions ?? [];

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "64rem" }}>
      <h1>Dashboard</h1>

      <p>
        <Link to="/intakes/new">Create Intake</Link>
      </p>
      <p>
        <Link to="/review-queue">Open Review Queue</Link>
      </p>

      {latestCompletedAnalysis && (
        <>
          <h2>Latest Completed Analysis</h2>
          <article style={{ marginBottom: "2rem" }}>
            <h3>
              <Link to={`/analyses/${latestCompletedAnalysis.analysis_id}`}>
                {latestCompletedAnalysis.customer_name} — {latestCompletedAnalysis.environment_name}
              </Link>
            </h3>
            <p>Analysis ID: {latestCompletedAnalysis.analysis_id}</p>
            <p>Status: {latestCompletedAnalysis.overall_status}</p>
            <StatusHelp status={latestCompletedAnalysis.overall_status} />
            <p>Completed: {formatUnixSeconds(latestCompletedAnalysis.analysis_date)}</p>
            <p>
              Applies: {latestCompletedAnalysis.applies_count} | Review Required:{" "}
              {latestCompletedAnalysis.review_required_count} | Unknown:{" "}
              {latestCompletedAnalysis.unknown_count} | Blocked:{" "}
              {latestCompletedAnalysis.blocked_count}
            </p>
            <p>Applications in Scope: {latestCompletedAnalysis.applications_count}</p>
          </article>
        </>
      )}

      {topRisks.length > 0 && (
        <>
          <h2>Top Risks</h2>
          <ul>
            {topRisks.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}

      {topActions.length > 0 && (
        <>
          <h2>Top Actions</h2>
          <ul>
            {topActions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}

      <h2>Latest Analyses</h2>
      {data.analyses.map((analysis) => (
        <article key={analysis.analysis_id} style={{ marginBottom: "1.5rem" }}>
          <h3>
            <Link to={`/analyses/${analysis.analysis_id}`}>
              {analysis.customer_name} — {analysis.environment_name}
            </Link>
          </h3>
          <p>Analysis ID: {analysis.analysis_id}</p>
          <p>Status: {analysis.overall_status}</p>
          <StatusHelp status={analysis.overall_status} />
          <p>
            Applies: {analysis.applies_count} | Review Required: {analysis.review_required_count} | Unknown:{" "}
            {analysis.unknown_count} | Blocked: {analysis.blocked_count}
          </p>
          <p>Applications in Scope: {analysis.applications_count}</p>
          <p>
            Analysis Date: {formatUnixSeconds(analysis.analysis_date)}
          </p>
        </article>
      ))}
    </main>
  );
}