import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { formatStatusLabel } from "../utils/status";
import StatusHelp from "../components/StatusHelp";
import { formatUnixSeconds } from "../utils/time";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import { getAnalysisOverview, type AnalysisOverviewResponse } from "../services/analyses";

function SectionList({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  if (items.length === 0) return null;

  return (
    <section style={{ marginBottom: "2rem" }}>
      <h2>{title}</h2>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function SummaryCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div
      style={{
        border: "1px solid #ccc",
        padding: "0.75rem 1rem",
        minWidth: "10rem",
      }}
    >
      <div style={{ fontSize: "0.9rem" }}>{label}</div>
      <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>{value}</div>
    </div>
  );
}

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

  const topRisks = data.top_risks ?? [];
  const topActions = data.top_actions ?? [];

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: "64rem" }}>
      <h1>Analysis Overview</h1>

      <p>
        <Link to="/dashboard">Back to Dashboard</Link>
      </p>

      <section style={{ marginBottom: "2rem" }}>
        <p>Analysis ID: {data.analysis_id}</p>
        <p>
          {data.customer_name} — {data.environment_name}
        </p>
        <p>Status: {formatStatusLabel(data.overall_status)}</p>
        <StatusHelp status={data.overall_status} />
        <p>Started: {formatUnixSeconds(data.started_utc)}</p>
        <p>Completed: {formatUnixSeconds(data.completed_utc)}</p>
        <p>Duration (ms): {data.duration_ms ?? "N/A"}</p>
        {reviewNote && <p>{reviewNote}</p>}
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Summary</h2>
        <div
          style={{
            display: "flex",
            gap: "1rem",
            flexWrap: "wrap",
          }}
        >
          <SummaryCard label="Applies" value={data.summary.applies_count} />
          <SummaryCard label="Requires Review" value={data.summary.review_required_count} />
          <SummaryCard label="Unknown" value={data.summary.unknown_count} />
          <SummaryCard label="Blocked" value={data.summary.blocked_count} />
        </div>
      </section>

      <SectionList title="Top Risks" items={topRisks} />
      <SectionList title="Top Actions" items={topActions} />
      <SectionList title="Assumptions" items={data.assumptions} />
      <SectionList title="Missing Inputs" items={data.missing_inputs} />
      <SectionList title="Derived Risks" items={data.derived_risks} />

      <section>
        <h2>Applications</h2>
        <ul>
          {data.applications.map((app) => (
            <li key={app.analysis_application_id} style={{ marginBottom: "1rem" }}>
              <div>
                <Link to={`/analyses/${data.analysis_id}/applications/${app.analysis_application_id}`}>
                  {app.application_name}
                </Link>{" "}
                — {app.status}
              </div>
              <div>
                Current: {app.current_version} | Target: {app.target_version} | Findings:{" "}
                {app.findings_count}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}